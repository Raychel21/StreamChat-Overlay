import os
import time
import re
import json
import html
import hashlib
import asyncio
import requests
from PySide6.QtCore import QThread, Signal


# ── Emote Cache Directory ──────────────────────────────────────────────────────
EMOTES_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "emotes_cache"
)


def _get_or_download_emote(img_url: str, session=None) -> str | None:
    """Download dan simpan thumbnail emote ke cache lokal."""
    try:
        if not img_url:
            return None
        os.makedirs(EMOTES_CACHE_DIR, exist_ok=True)
        url_hash = hashlib.md5(img_url.encode("utf-8")).hexdigest()
        target_path = os.path.join(EMOTES_CACHE_DIR, f"{url_hash}.png")

        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return target_path

        s = session or requests
        r = s.get(img_url, timeout=4)
        if r.status_code == 200 and r.content:
            with open(target_path, "wb") as f:
                f.write(r.content)
            return target_path
    except Exception as e:
        print(f"[ChatWorker] Gagal unduh emote ({img_url[:30]}...): {e}")
    return None


# ── HTTP Headers ───────────────────────────────────────────────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_YT_CLIENT_CONTEXT = {
    "context": {
        "client": {
            "clientName": "WEB",
            "clientVersion": "2.20240101.00.00",
            "hl": "en",
            "gl": "US",
        }
    }
}


class ChatWorker(QThread):
    """
    Worker thread untuk mengambil live chat YouTube dan TikTok.

    Signals:
        chat_received(author, message, is_superchat, amount, platform)
        pinned_chat_received(author, message)
        viewer_count_updated(count)
        error_occurred(error_message)
        status_updated(status_message)
    """
    chat_received        = Signal(str, str, bool, str, str)
    pinned_chat_received = Signal(str, str)
    viewer_count_updated = Signal(int)
    error_occurred       = Signal(str)
    status_updated       = Signal(str)

    def __init__(self, connection_type="stream_url", stream_url="",
                 livechat_url="", parent=None):
        super().__init__(parent)
        self.connection_type = connection_type
        self.stream_url      = stream_url
        self.livechat_url    = livechat_url
        self.running         = True
        self._session        = requests.Session()
        self._session.headers.update(_HEADERS)
        self._emitted_pinned = None  # Hindari emit pinned berulang
        self._tiktok_client  = None  # Referensi ke TikTokLiveClient
        self._loop           = None  # asyncio event loop untuk TikTok

    def update_config(self, connection_type, stream_url, livechat_url):
        self.connection_type = connection_type
        self.stream_url      = stream_url
        self.livechat_url    = livechat_url

    # ── URL Detection ─────────────────────────────────────────────────────────
    def _detect_platform(self, url: str) -> str:
        """Deteksi platform dari URL: 'youtube', 'tiktok', atau 'unknown'."""
        url_lower = url.lower()
        if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
            return "tiktok"
        if any(x in url_lower for x in ("youtube.com", "youtu.be", "live_chat")):
            return "youtube"
        return "unknown"

    # ── Main Run ──────────────────────────────────────────────────────────────
    def run(self):
        target_url = (
            self.stream_url if self.connection_type == "stream_url"
            else self.livechat_url
        )
        platform = self._detect_platform(target_url)

        if platform == "tiktok":
            self._run_tiktok(target_url)
        else:
            # Coba YouTube
            video_id = self._extract_video_id(target_url)
            if video_id:
                print(f"[ChatWorker] YouTube Video ID: {video_id}")
                self.status_updated.emit(f"✅ Menghubungkan ke ID: {video_id}...")
                self._run_youtube_live_chat(video_id)
            else:
                msg = "❌ Video ID tidak ditemukan. Pastikan format URL benar."
                print(f"[ChatWorker] {msg}")
                self.error_occurred.emit(msg)

    # ─────────────────────────────────────────────────────────────────────────
    # ██████   TikTok Live Chat
    # ─────────────────────────────────────────────────────────────────────────
    def _extract_tiktok_username(self, url: str) -> str | None:
        """
        Ekstrak username TikTok dari berbagai format URL.
        - https://www.tiktok.com/@username/live
        - https://www.tiktok.com/@username
        - https://vt.tiktok.com/XXXXX/ (short URL → resolve dulu)
        - Username langsung (misal: '@username' atau 'username')
        """
        # Username langsung (bukan URL)
        if not url.startswith("http"):
            return url.lstrip("@").strip() or None

        # tiktok.com/@username pattern
        m = re.search(r"tiktok\.com/@([A-Za-z0-9_.]+)", url)
        if m:
            return m.group(1)

        # Short URL → resolve redirect
        if "vt.tiktok.com" in url or re.match(r"https?://[^/]*tiktok\.com/[A-Za-z0-9]+", url):
            try:
                self.status_updated.emit("🔗 Memproses short URL TikTok...")
                r = self._session.get(url.strip("/"), timeout=10,
                                      allow_redirects=True)
                final_url = r.url
                m2 = re.search(r"tiktok\.com/@([A-Za-z0-9_.]+)", final_url)
                if m2:
                    return m2.group(1)
                # Coba dari redirect history
                for resp in r.history:
                    loc = resp.headers.get("Location", "")
                    m3 = re.search(r"tiktok\.com/@([A-Za-z0-9_.]+)", loc)
                    if m3:
                        return m3.group(1)
                # Coba dari response text
                m4 = re.search(r'"uniqueId"\s*:\s*"([^"]+)"', r.text)
                if m4:
                    return m4.group(1)
            except Exception as e:
                print(f"[ChatWorker] Gagal resolve TikTok short URL: {e}")
        return None

    def _run_tiktok(self, url: str):
        """Jalankan TikTok live chat menggunakan TikTokLive library."""
        username = self._extract_tiktok_username(url)
        if not username:
            self.error_occurred.emit(
                "❌ Username TikTok tidak ditemukan.\n"
                "Gunakan format: https://www.tiktok.com/@username/live\n"
                "atau masukkan @username langsung."
            )
            return

        self.status_updated.emit(f"🎵 Menghubungkan ke TikTok @{username}...")

        # Jalankan asyncio loop di thread ini
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._tiktok_async(username))
        except Exception as e:
            if self.running:
                print(f"[ChatWorker] TikTok error: {e}")
                self.error_occurred.emit(f"❌ TikTok Error: {str(e)[:150]}")
        finally:
            try:
                self._loop.close()
            except Exception:
                pass
            self._loop = None

    async def _tiktok_async(self, username: str):
        """Async handler utama untuk TikTok live chat."""
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import (
            ConnectEvent, DisconnectEvent, CommentEvent,
            GiftEvent, JoinEvent, LiveEndEvent,
        )

        retry_count = 0
        max_retries = 5

        while self.running and retry_count <= max_retries:
            client = TikTokLiveClient(unique_id=username)
            self._tiktok_client = client

            @client.on(ConnectEvent)
            async def on_connect(event: ConnectEvent):
                self.status_updated.emit(f"✅ TikTok @{username} terhubung!")
                nonlocal retry_count
                retry_count = 0

            @client.on(CommentEvent)
            async def on_comment(event: CommentEvent):
                if not self.running:
                    return
                try:
                    author = (
                        getattr(event.user, "nickname", None)
                        or getattr(event.user, "unique_id", None)
                        or "TikTokUser"
                    )
                    msg = getattr(event, "comment", "") or ""
                    if author and msg:
                        self.chat_received.emit(str(author), str(msg), False, "", "TikTok")
                except Exception as e:
                    print(f"[ChatWorker] TikTok comment parse error: {e}")

            @client.on(GiftEvent)
            async def on_gift(event: GiftEvent):
                if not self.running:
                    return
                try:
                    author = (
                        getattr(event.user, "nickname", None)
                        or getattr(event.user, "unique_id", None)
                        or "TikTokUser"
                    )
                    gift_name  = getattr(event.gift, "name", "Gift") or "Gift"
                    gift_count = getattr(event, "repeat_count", 1) or 1
                    msg        = f"🎁 {gift_name} ×{gift_count}"
                    if author:
                        self.chat_received.emit(str(author), str(msg), True, f"×{gift_count}", "TikTok")
                except Exception as e:
                    print(f"[ChatWorker] TikTok gift parse error: {e}")

            @client.on(JoinEvent)
            async def on_join(event: JoinEvent):
                if not self.running:
                    return
                try:
                    count = getattr(event, "viewer_count", None)
                    if count is not None:
                        self.viewer_count_updated.emit(int(count))
                except Exception:
                    pass

            @client.on(LiveEndEvent)
            async def on_end(event: LiveEndEvent):
                print(f"[ChatWorker] TikTok live ended for @{username}")
                if client.connected:
                    await client.disconnect()

            @client.on(DisconnectEvent)
            async def on_disconnect(event: DisconnectEvent):
                print(f"[ChatWorker] TikTok disconnected from @{username}")

            try:
                await client.connect()
            except Exception as e:
                err_str = str(e)
                print(f"[ChatWorker] TikTok connect error: {err_str}")

                if not self.running:
                    break

                retry_count += 1
                if retry_count > max_retries:
                    self.error_occurred.emit(
                        f"❌ Gagal terhubung ke TikTok @{username}.\n"
                        "Pastikan stream sedang live dan username benar."
                    )
                    break

                msg = f"⚠️ TikTok retry {retry_count}/{max_retries}..."
                self.status_updated.emit(msg)

                # Interruptible sleep
                for _ in range(80):
                    if not self.running:
                        break
                    await asyncio.sleep(0.1)

            finally:
                try:
                    if client.connected:
                        await client.disconnect()
                except Exception:
                    pass
                self._tiktok_client = None

    # ─────────────────────────────────────────────────────────────────────────
    # ██████   YouTube Live Chat
    # ─────────────────────────────────────────────────────────────────────────

    # ── Video ID Extraction ────────────────────────────────────────────────────
    def _extract_video_id(self, url: str) -> str | None:
        if not url:
            return None
        patterns = [
            r"(?:v=|/watch\?v=)([a-zA-Z0-9_-]{11})",
            r"/live/([a-zA-Z0-9_-]{11})",
            r"/embed/([a-zA-Z0-9_-]{11})",
            r"live_chat\?(?:.*&)?v=([a-zA-Z0-9_-]{11})",
            r"youtu\.be/([a-zA-Z0-9_-]{11})",
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1).split("?")[0].split("&")[0]
        return None

    # ── YouTube Live Chat Loop ─────────────────────────────────────────────────
    def _run_youtube_live_chat(self, video_id: str):
        retry_count = 0
        max_retries = 5

        while self.running and retry_count <= max_retries:
            try:
                continuation, api_key = self._fetch_initial_data(video_id)

                if not continuation:
                    retry_count += 1
                    if retry_count > max_retries:
                        self.error_occurred.emit(
                            "❌ Gagal mendapatkan data live chat. "
                            "Pastikan stream sedang live dan URL benar."
                        )
                        return
                    msg = f"⚠️ Menunggu stream aktif... ({retry_count}/{max_retries})"
                    print(f"[ChatWorker] {msg}")
                    self.status_updated.emit(msg)
                    time.sleep(10)
                    continue

                print(f"[ChatWorker] Berhasil! Token: {continuation[:30]}...")
                self.status_updated.emit("✅ Live chat terhubung!")
                retry_count = 0

                tick = 0
                while self.running:
                    messages, new_cont, timeout_ms = self._fetch_chat_messages(
                        continuation, api_key
                    )

                    for (author, msg, is_sc, amount) in messages:
                        if not self.running:
                            break
                        self.chat_received.emit(author, msg, is_sc, amount, "YouTube")

                    if new_cont:
                        continuation = new_cont
                    else:
                        print("[ChatWorker] Tidak ada continuation baru.")
                        break

                    tick += 1
                    if tick % 30 == 0 or tick == 2:
                        count = self._fetch_viewer_count(video_id)
                        if count is not None:
                            self.viewer_count_updated.emit(count)

                    wait_s  = max(1.0, min((timeout_ms or 5000) / 1000.0, 8.0))
                    elapsed = 0.0
                    while self.running and elapsed < wait_s:
                        time.sleep(0.3)
                        elapsed += 0.3

                if self.running:
                    retry_count += 1
                    self.status_updated.emit(
                        f"⚠️ Stream berakhir, mencoba ulang ({retry_count}/{max_retries})..."
                    )
                    time.sleep(10)

            except requests.exceptions.ConnectionError as e:
                retry_count += 1
                print(f"[ChatWorker] Koneksi gagal: {e}")
                self.status_updated.emit(
                    f"⚠️ Koneksi terputus ({retry_count}/{max_retries}), mencoba ulang..."
                )
                time.sleep(8)
            except Exception as e:
                retry_count += 1
                print(f"[ChatWorker] Error tidak terduga: {e}")
                if retry_count > max_retries:
                    self.error_occurred.emit(f"❌ Error: {str(e)[:120]}")
                    return
                time.sleep(5)

        print("[ChatWorker] Worker selesai.")

    # ── Fetch Initial Data ─────────────────────────────────────────────────────
    def _fetch_initial_data(self, video_id: str) -> tuple:
        url = f"https://www.youtube.com/live_chat?v={video_id}&is_popout=1"
        try:
            r    = self._session.get(url, timeout=15)
            html_text = r.text

            # API Key
            api_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
            m_key   = re.search(r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"', html_text)
            if m_key:
                api_key = m_key.group(1)

            # Ekstrak ytInitialData JSON
            data = self._extract_json_from_page(html_text, "ytInitialData")
            if data is None:
                print("[ChatWorker] ytInitialData tidak dapat di-parse.")
                return None, api_key

            continuation = self._find_continuation_recursive(data, depth=0)
            return continuation, api_key

        except Exception as e:
            print(f"[ChatWorker] Error fetch initial data: {e}")
            return None, None

    def _extract_json_from_page(self, html_text: str, var_name: str) -> dict | None:
        """Ekstrak JSON object yang terikat ke JS variable di halaman HTML."""
        name_escaped = re.escape(var_name)
        candidates   = [
            name_escaped + r'"\]\s*=\s*\{',  # ytInitialData"] = {
            name_escaped + r'"\s*=\s*\{',    # ytInitialData" = {
            name_escaped + r'\s*=\s*\{',     # ytInitialData = {
        ]
        start_pos = None
        for pat in candidates:
            m = re.search(pat, html_text)
            if m:
                start_pos = m.end() - 1
                break

        if start_pos is None:
            return None

        depth       = 0
        in_string   = False
        escape_next = False

        for i in range(start_pos, len(html_text)):
            ch = html_text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html_text[start_pos : i + 1])
                    except json.JSONDecodeError:
                        return None
        return None

    def _find_continuation_recursive(self, obj, depth: int) -> str | None:
        if depth > 10:
            return None
        cont_keys = (
            "timedContinuationData",
            "invalidationContinuationData",
            "liveChatReplayContinuationData",
            "playerSeekContinuationData",
        )
        if isinstance(obj, dict):
            for key in cont_keys:
                if key in obj:
                    token = obj[key].get("continuation") or obj[key].get("token")
                    if token and isinstance(token, str) and len(token) > 20:
                        return token
            for val in obj.values():
                res = self._find_continuation_recursive(val, depth + 1)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_continuation_recursive(item, depth + 1)
                if res:
                    return res
        return None

    # ── Fetch Chat Messages ────────────────────────────────────────────────────
    def _fetch_chat_messages(self, continuation: str, api_key: str) -> tuple:
        url     = f"https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key={api_key}"
        payload = {**_YT_CLIENT_CONTEXT, "continuation": continuation}

        try:
            r    = self._session.post(url, json=payload, timeout=12)
            data = r.json()
        except Exception as e:
            print(f"[ChatWorker] Error fetch messages: {e}")
            return [], continuation, 5000

        messages   = []
        new_cont   = None
        timeout_ms = 5000

        try:
            live_chat = (
                data.get("continuationContents", {})
                    .get("liveChatContinuation", {})
            )

            # Continuation baru
            for c in live_chat.get("continuations", []):
                for key in ("timedContinuationData", "invalidationContinuationData"):
                    if key in c:
                        new_cont   = c[key].get("continuation") or c[key].get("token")
                        timeout_ms = c[key].get("timeoutMs", 5000)
                        break
                if new_cont:
                    break

            # Proses actions
            for action in live_chat.get("actions", []):

                # ── Pesan chat biasa ────────────────────────────────────
                item  = action.get("addChatItemAction", {}).get("item", {})

                txt_r = item.get("liveChatTextMessageRenderer")
                if txt_r:
                    author = self._get_simple_text(txt_r.get("authorName", {}))
                    msg    = self._get_runs_text(txt_r.get("message", {}), self._session)
                    if author:
                        messages.append((author, msg, False, ""))

                sc_r = item.get("liveChatPaidMessageRenderer")
                if sc_r:
                    author = self._get_simple_text(sc_r.get("authorName", {}))
                    msg    = self._get_runs_text(sc_r.get("message", {}), self._session)
                    amount = self._get_simple_text(sc_r.get("purchaseAmountText", {}))
                    messages.append((author or "—", msg, True, amount or ""))

                mem_r = item.get("liveChatMembershipItemRenderer")
                if mem_r:
                    author = self._get_simple_text(mem_r.get("authorName", {}))
                    header = self._get_runs_text(mem_r.get("headerSubtext", {}), self._session)
                    if author:
                        messages.append((author, f"🎉 {header}", False, ""))

                # ── Pinned / Banner message ─────────────────────────────
                banner_cmd = action.get("addBannerToLiveChatCommand", {})
                if banner_cmd:
                    banner_r = (banner_cmd
                                .get("bannerRenderer", {})
                                .get("liveChatBannerRenderer", {}))
                    if banner_r:
                        contents = banner_r.get("contents", {})
                        for rkey in (
                            "liveChatTextMessageRenderer",
                            "liveChatPaidMessageRenderer",
                        ):
                            renderer = contents.get(rkey)
                            if renderer:
                                author  = self._get_simple_text(renderer.get("authorName", {}))
                                msg     = self._get_runs_text(renderer.get("message", {}), self._session)
                                pin_key = f"{author}:{msg}"
                                if author and pin_key != self._emitted_pinned:
                                    self._emitted_pinned = pin_key
                                    self.pinned_chat_received.emit(author, msg)
                                break

                # Dismiss banner (pesan pinned dilepas)
                if "removeBannerForLiveChatCommand" in action:
                    self._emitted_pinned = None
                    self.pinned_chat_received.emit("", "")

        except Exception as e:
            print(f"[ChatWorker] Error parse messages: {e}")

        return messages, new_cont, timeout_ms

    # ── Text Extraction Helpers ────────────────────────────────────────────────
    @staticmethod
    def _get_simple_text(obj: dict) -> str:
        return obj.get("simpleText", "") if isinstance(obj, dict) else ""

    @staticmethod
    def _get_runs_text(obj: dict, session=None) -> str:
        """
        Gabungkan text dari runs array YouTube.
        Menangani:
        - Text biasa (di-escape untuk HTML)
        - Emote YouTube / Membership: download/cache gambar & tampilkan visual <img src="...">
        - Unicode emoji (pass-through)
        """
        if not isinstance(obj, dict):
            return ""
        parts = []
        for run in obj.get("runs", []):
            if "text" in run:
                parts.append(html.escape(run["text"]))
            elif "emoji" in run:
                emoji      = run["emoji"]
                emoji_id   = emoji.get("emojiId", "")
                shortcuts  = emoji.get("shortcuts", [])
                is_custom  = emoji.get("isCustomEmoji", False)
                image      = emoji.get("image", {})
                thumbnails = image.get("thumbnails", []) if isinstance(image, dict) else []

                img_tag = None
                if thumbnails:
                    img_url = thumbnails[0].get("url")
                    if img_url:
                        local_path = _get_or_download_emote(img_url, session)
                        if local_path:
                            file_uri = local_path.replace("\\", "/")
                            img_tag = f'<img src="file:///{file_uri}" width="22" height="22" style="vertical-align:middle;">'

                if img_tag:
                    parts.append(img_tag)
                else:
                    if not is_custom and emoji_id and "/" not in emoji_id and len(emoji_id) <= 8:
                        parts.append(emoji_id)
                    elif shortcuts:
                        raw   = shortcuts[0]
                        clean = raw.strip(":")
                        if clean.startswith("_"):
                            clean = clean[1:]
                        parts.append(f"[{html.escape(clean)}]")
                    elif emoji_id:
                        name = emoji_id.split("/")[-1]
                        parts.append(f"[{html.escape(name[:20])}]")

        return "".join(parts)

    # ── Viewer Count ──────────────────────────────────────────────────────────
    def _fetch_viewer_count(self, video_id: str) -> int | None:
        try:
            r = self._session.get(
                f"https://www.youtube.com/watch?v={video_id}", timeout=8
            )
            m = re.search(r'"concurrentViewers":"(\d+)"', r.text)
            if m:
                return int(m.group(1))
            m = re.search(
                r'"viewCount":\{"videoViewCountRenderer":\{"viewCount":\{"simpleText":"([\d,\.]+)',
                r.text,
            )
            if m:
                s = re.sub(r"[^\d]", "", m.group(1))
                return int(s) if s else None
        except Exception as e:
            print(f"[ChatWorker] Gagal ambil viewer count: {e}")
        return None

    # ── Stop ──────────────────────────────────────────────────────────────────
    def stop(self):
        self.running = False

        # Stop TikTok client jika aktif
        if self._tiktok_client is not None and self._loop is not None:
            try:
                if self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._tiktok_client.disconnect(), self._loop
                    )
            except Exception as e:
                print(f"[ChatWorker] TikTok stop error: {e}")

        try:
            self._session.close()
        except Exception:
            pass
        self.wait(6000)
