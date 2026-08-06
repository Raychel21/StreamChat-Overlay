import queue
from PySide6.QtCore import QThread


# ─── Language Detection (tanpa library eksternal) ──────────────────────────────
_INDO_WORDS = {
    "yang", "dan", "ini", "itu", "untuk", "dari", "dengan", "ke", "di", "ada",
    "tidak", "saya", "aku", "kamu", "kita", "apa", "bisa", "juga", "sudah",
    "akan", "atau", "tapi", "kalau", "karena", "jadi", "nih", "sih", "deh",
    "dong", "loh", "wkwk", "haha", "makasih", "selamat", "mantap", "keren",
    "oke", "gini", "gitu", "gimana", "kenapa", "siapa", "mana", "belum",
    "lagi", "sama", "banget", "udah", "baru", "mau", "kayak", "emang",
}


def _detect_language(text: str) -> str:
    """
    Deteksi bahasa: 'ja' (Jepang), 'id' (Indonesia), 'en' (Inggris).
    Menggunakan heuristic berbasis karakter dan kata kunci tanpa library eksternal.
    """
    if not text.strip():
        return "en"

    # Hitung karakter Jepang (Hiragana, Katakana, Kanji CJK)
    ja_count = sum(
        1 for c in text
        if "\u3040" <= c <= "\u30ff"   # Hiragana & Katakana
        or "\u4e00" <= c <= "\u9fff"   # Kanji (CJK Unified)
        or "\uff00" <= c <= "\uffef"   # Halfwidth/Fullwidth forms
    )
    if ja_count > 0:
        return "ja"

    # Deteksi Indonesia berdasarkan kata kunci umum
    words     = set(text.lower().split())
    indo_hits = len(words & _INDO_WORDS)
    if indo_hits >= 2 or (indo_hits >= 1 and len(words) <= 4):
        return "id"

    return "en"


# ─── TTS Engine ────────────────────────────────────────────────────────────────
class TTSEngine(QThread):
    """
    Text-To-Speech engine yang berjalan di thread terpisah.
    Menggunakan pyttsx3 dengan pemilihan suara otomatis berdasarkan bahasa:
    - Bahasa Jepang  → suara Japanese jika tersedia, sinon skip
    - Bahasa Indonesia → suara Indonesian jika tersedia, sinon English fallback
    - Bahasa Inggris  → suara English (default)
    """

    def __init__(self, speed: int = 170, volume: float = 0.8, parent=None):
        super().__init__(parent)
        self._queue  = queue.Queue()
        self.running = True
        self.speed   = speed
        self.volume  = volume

    def set_settings(self, speed: int, volume: float):
        self.speed  = speed
        self.volume = volume

    def speak(self, author: str, message: str):
        """Antri pesan untuk dibacakan. Non-blocking."""
        self._queue.put((author, message))

    def run(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
        except Exception as e:
            print(f"[TTSEngine] Gagal inisialisasi pyttsx3: {e}")
            return

        # ── Inventarisasi suara yang tersedia ────────────────────────────
        voices_by_lang: dict[str, str] = {}  # lang_code -> voice.id
        try:
            for voice in engine.getProperty("voices"):
                vid   = (voice.id or "").lower()
                vname = (voice.name or "").lower()

                # Deteksi Japanese voice
                if "ja" not in voices_by_lang:
                    if any(k in vname or k in vid for k in
                           ("japanese", "ja_jp", "ja-jp", "haruka", "zira-ja",
                            "naoko", "ichiro", "kyoko", "otoya")):
                        voices_by_lang["ja"] = voice.id
                        print(f"[TTSEngine] Suara Jepang ditemukan: {voice.name}")

                # Deteksi Indonesian voice
                if "id" not in voices_by_lang:
                    if any(k in vname or k in vid for k in
                           ("indonesia", "id_id", "id-id", "andika", "damayanti")):
                        voices_by_lang["id"] = voice.id
                        print(f"[TTSEngine] Suara Indonesia ditemukan: {voice.name}")

                # Deteksi English voice (default fallback)
                if "en" not in voices_by_lang:
                    if any(k in vname or k in vid for k in
                           ("english", "en_us", "en-us", "en_gb", "en-gb",
                            "david", "zira", "mark", "hazel", "george")):
                        voices_by_lang["en"] = voice.id
                        print(f"[TTSEngine] Suara Inggris ditemukan: {voice.name}")

        except Exception as e:
            print(f"[TTSEngine] Error enumerasi suara: {e}")

        # Fallback: gunakan voice default jika tidak ada yang terdeteksi
        if "en" not in voices_by_lang:
            try:
                default_voices = engine.getProperty("voices")
                if default_voices:
                    voices_by_lang["en"] = default_voices[0].id
            except Exception:
                pass

        default_voice = voices_by_lang.get("en")
        print(f"[TTSEngine] Peta suara: {list(voices_by_lang.keys())}")

        # ── Loop utama ───────────────────────────────────────────────────
        item = None
        while self.running:
            try:
                item = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            # Sentinel untuk stop
            if item is None:
                try:
                    self._queue.task_done()
                except ValueError:
                    pass
                break

            try:
                author, message = item
                lang = _detect_language(message)

                # Skip Jepang jika tidak ada suara Jepang (bunyi-bunyian tidak enak)
                if lang == "ja" and "ja" not in voices_by_lang:
                    print(f"[TTSEngine] Skip teks Jepang (tidak ada suara ja)")
                    self._queue.task_done()
                    continue

                # Pilih voice
                voice_id = voices_by_lang.get(lang, default_voice)
                if voice_id:
                    engine.setProperty("voice", voice_id)

                engine.setProperty("rate", self.speed)
                engine.setProperty("volume", self.volume)

                # Teks yang dibaca berbeda per bahasa
                if lang == "en":
                    text = f"{author} says {message}"
                elif lang == "id":
                    text = f"{author} bilang {message}"
                else:  # ja
                    text = message  # Baca pesan saja, nama author bisa tidak natural

                engine.say(text)
                engine.runAndWait()

            except Exception as e:
                print(f"[TTSEngine] Error TTS: {e}")
            finally:
                try:
                    self._queue.task_done()
                except ValueError:
                    pass

        # Bersihkan
        try:
            engine.stop()
        except Exception:
            pass

    def stop(self):
        """Hentikan TTS engine dengan aman."""
        self.running = False
        self._queue.put(None)   # sentinel untuk unlock blocking get()
        self.wait(3000)
