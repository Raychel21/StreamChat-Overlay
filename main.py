import sys
import re
import ctypes
import hashlib
import colorsys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QPushButton, QSlider, QCheckBox, QComboBox,
                             QLineEdit, QRadioButton, QGroupBox, QStackedWidget,
                             QSizeGrip, QFrame)
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QEvent
from PySide6.QtGui import QFont, QFontMetrics

import config_manager
from style_sheets import THEMES, MAIN_APP_STYLES, get_theme_qss
from filter_engine import FilterEngine
from tts_engine import TTSEngine
from chat_worker import ChatWorker


# ─── Windows API helpers ──────────────────────────────────────────────────────
GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020


def _set_click_through(widget, enable: bool):
    """Toggle click-through di level Windows API (paling reliable di Windows)."""
    try:
        hwnd = int(widget.winId())
        ex = ctypes.windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        if enable:
            ex |= (WS_EX_LAYERED | WS_EX_TRANSPARENT)
        else:
            ex &= ~WS_EX_TRANSPARENT
            ex |= WS_EX_LAYERED
        ctypes.windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex)
    except Exception as e:
        print(f"[WinAPI] click-through error: {e}")


# ─── Author color helper ──────────────────────────────────────────────────────
_PALETTE = [
    "#00F0FF", "#FF7700", "#FF007F", "#00FF66",
    "#FCEE0A", "#A855F7", "#38BDF8", "#F43F5E",
    "#10B981", "#EAB308", "#EC4899", "#6366F1",
    "#2DD4BF", "#FB923C", "#F472B6", "#A7F3D0"
]

def _author_color(name: str) -> str:
    """Pilih warna konsisten untuk nama author dari palette."""
    idx = int(hashlib.md5(name.encode("utf-8", errors="replace")).hexdigest()[:8], 16)
    return _PALETTE[idx % len(_PALETTE)]


# ─────────────────────────────────────────────────────────────────────────────
class OverlayWindow(QWidget):
    """
    Overlay Chat – always on top, frameless.
    * MainWindow AKTIF  → bisa drag & resize
    * MainWindow MINIMIZE → click-through (Windows API), tidak mengganggu app lain
    """

    def __init__(self, config):
        super().__init__(None)
        self.config       = config
        self._drag_pos    = QPoint()
        self._interactive = True

        flags = (Qt.Window | Qt.WindowStaysOnTopHint
                 | Qt.FramelessWindowHint | Qt.Tool)
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(240, 200)
        self.resize(390, 570)

        self._build_ui()
        self.apply_theme()

    # ── Show event ─────────────────────────────────────────────────────────
    def showEvent(self, event):
        super().showEvent(event)
        # Saat show, MainWindow pasti aktif → overlay harus interactive
        QTimer.singleShot(120, lambda: _set_click_through(self, False))

    # ── Interactive toggle ─────────────────────────────────────────────────
    def set_interactive(self, interactive: bool):
        """
        True  → MainWindow aktif → overlay selalu bisa drag/resize
        False → MainWindow minimize → overlay click-through
        """
        self._interactive = interactive
        _set_click_through(self, not interactive)
        if hasattr(self, "_grip"):
            self._grip.setVisible(interactive)

    # ── UI Builder ─────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.container = QWidget()
        self.container.setObjectName("CentralWidget")
        cl = QVBoxLayout(self.container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────
        self.header = QWidget()
        self.header.setObjectName("HeaderBar")
        self.header.setFixedHeight(36)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(10, 4, 10, 4)

        self.lbl_title = QLabel("🔴 LIVE CHAT")
        self.lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        hl.addWidget(self.lbl_title)
        hl.addStretch()

        self.badge_viewers = QLabel("👁️ —")
        self.badge_viewers.setObjectName("ViewerBadge")
        self.badge_viewers.setVisible(self.config.get("show_viewer_count", True))
        hl.addWidget(self.badge_viewers)
        cl.addWidget(self.header)

        # ── Pinned Message Area (hidden by default) ──────────────────────
        self.pinned_container = QWidget()
        self.pinned_container.setObjectName("PinnedContainer")
        pinned_layout = QVBoxLayout(self.pinned_container)
        pinned_layout.setContentsMargins(8, 6, 8, 6)
        pinned_layout.setSpacing(3)

        pin_header_row = QHBoxLayout()
        lbl_pin_icon = QLabel("📌 PINNED")
        lbl_pin_icon.setObjectName("PinLabel")
        lbl_pin_icon.setFont(QFont("Segoe UI", 8, QFont.Bold))
        pin_header_row.addWidget(lbl_pin_icon)
        pin_header_row.addStretch()
        pinned_layout.addLayout(pin_header_row)

        self.lbl_pinned_author = QLabel("")
        self.lbl_pinned_author.setObjectName("PinnedAuthor")
        self.lbl_pinned_author.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_pinned_author.setWordWrap(False)
        pinned_layout.addWidget(self.lbl_pinned_author)

        self.lbl_pinned_msg = QLabel("")
        self.lbl_pinned_msg.setObjectName("PinnedMessage")
        self.lbl_pinned_msg.setFont(QFont("Segoe UI", 9))
        self.lbl_pinned_msg.setWordWrap(True)
        self.lbl_pinned_msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        pinned_layout.addWidget(self.lbl_pinned_msg)

        self.pinned_container.hide()
        cl.addWidget(self.pinned_container)

        # ── Divider setelah pinned (hidden by default) ───────────────────
        self.pinned_divider = QFrame()
        self.pinned_divider.setFrameShape(QFrame.HLine)
        self.pinned_divider.setObjectName("PinnedDivider")
        self.pinned_divider.hide()
        cl.addWidget(self.pinned_divider)

        # ── Chat List ────────────────────────────────────────────────────
        self.chat_list = QListWidget()
        self.chat_list.setWordWrap(True)
        self.chat_list.setFrameShape(QFrame.NoFrame)
        self.chat_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_list.setSpacing(2)
        self.chat_list.setUniformItemSizes(False)
        cl.addWidget(self.chat_list)

        # ── Resize grip ──────────────────────────────────────────────────
        grip_row = QHBoxLayout()
        grip_row.addStretch()
        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(16, 16)
        grip_row.addWidget(self._grip, 0, Qt.AlignBottom | Qt.AlignRight)
        grip_row.setContentsMargins(0, 0, 2, 2)
        cl.addLayout(grip_row)

        root.addWidget(self.container)

    # ── Drag via header ────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._interactive:
            if self.header.geometry().contains(event.position().toPoint()):
                self._drag_pos = (event.globalPosition().toPoint()
                                  - self.frameGeometry().topLeft())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() == Qt.LeftButton
                and self._interactive
                and not self._drag_pos.isNull()):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)

    # ── Resize event ────────────────────────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(80, self._refresh_all_item_sizes)

    def _refresh_all_item_sizes(self):
        vp_w = self.chat_list.viewport().width()
        if vp_w < 50:
            return
        for i in range(self.chat_list.count()):
            item   = self.chat_list.item(i)
            widget = self.chat_list.itemWidget(item)
            if widget:
                new_w = vp_w - 4
                widget.setFixedWidth(new_w)
                for child in widget.findChildren(QLabel):
                    child.setFixedWidth(new_w - 20)
                widget.adjustSize()
                h = widget.sizeHint().height()
                item.setSizeHint(QSize(new_w, h + 8))
        # Update lebar pinned message
        self.lbl_pinned_msg.setFixedWidth(
            max(100, self.pinned_container.width() - 16)
        )

    # ── Public API ────────────────────────────────────────────────────────
    def apply_theme(self):
        theme_name = self.config.get("theme", "Dark Neon")
        opacity    = self.config.get("opacity", 0.9)
        qss        = get_theme_qss(theme_name, opacity)
        self.container.setStyleSheet(qss)

    def update_config(self, config):
        self.config = config
        self.badge_viewers.setVisible(config.get("show_viewer_count", True))
        if self._interactive:
            _set_click_through(self, False)
        self.apply_theme()

    def set_pinned(self, author: str, msg: str):
        """Tampilkan pesan pinned di bagian atas overlay."""
        if not author and not msg:
            self.pinned_container.hide()
            self.pinned_divider.hide()
            return

        display_author = author if author.startswith("@") else f"@{author}"
        color = _author_color(author)
        self.lbl_pinned_author.setText(display_author)
        self.lbl_pinned_author.setStyleSheet(
            f"color:{color}; font-weight:bold; background:transparent;"
        )
        self.lbl_pinned_msg.setTextFormat(Qt.RichText)
        self.lbl_pinned_msg.setText(msg)
        self.lbl_pinned_msg.setFixedWidth(
            max(100, self.pinned_container.width() - 16)
        )
        self.pinned_container.show()
        self.pinned_divider.show()

    def add_chat(self, author: str, clean_msg: str, is_superchat: bool, amount: str):
        """Tambahkan item chat ke list. Username dan pesan mengalir secara inline (satu paragraph)."""
        font_size = self.config.get("font_size", 13)
        vp_w      = self.chat_list.viewport().width()
        avail_w   = max(200, vp_w - 4)
        inner_w   = avail_w - 20

        font_n = QFont()
        font_n.setFamilies(["Segoe UI", "Yu Gothic UI", "Meiryo", "Arial"])
        font_n.setPointSize(font_size)

        font_b = QFont()
        font_b.setFamilies(["Segoe UI", "Yu Gothic UI", "Meiryo", "Arial"])
        font_b.setPointSize(font_size)
        font_b.setBold(True)

        item_widget = QWidget()
        item_widget.setFixedWidth(avail_w)
        lo = QVBoxLayout(item_widget)
        lo.setContentsMargins(10, 4, 10, 4)
        lo.setSpacing(2)

        display_author = author if author.startswith("@") else f"@{author}"

        if is_superchat:
            item_widget.setStyleSheet(
                "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #FFD700,stop:1 #FF8C00);border-radius:8px;"
            )
            lbl_a = QLabel(f"⭐ {display_author}  —  {amount}")
            lbl_a.setFont(font_b)
            lbl_a.setStyleSheet("color:#000;background:transparent;")
            lbl_a.setWordWrap(True)
            lbl_a.setFixedWidth(inner_w)

            lbl_m = QLabel(clean_msg)
            lbl_m.setTextFormat(Qt.RichText)
            lbl_m.setFont(font_n)
            lbl_m.setStyleSheet("color:#111;font-weight:500;background:transparent;")
            lbl_m.setWordWrap(True)
            lbl_m.setFixedWidth(inner_w)
            lbl_m.setTextInteractionFlags(Qt.TextSelectableByMouse)

            lo.addWidget(lbl_a)
            lo.addWidget(lbl_m)
            lbl_m_h = _label_height(lbl_a, inner_w, font_size) + _label_height(lbl_m, inner_w, font_size)

        else:
            color = _author_color(author)
            html_msg = f'<span style="color:{color}; font-weight:bold;">{display_author}</span> {clean_msg}'

            lbl_m = QLabel(html_msg)
            lbl_m.setTextFormat(Qt.RichText)
            lbl_m.setFont(font_n)
            lbl_m.setStyleSheet("color:#E0E0E0;background:transparent;")
            lbl_m.setWordWrap(True)
            lbl_m.setFixedWidth(inner_w)
            lbl_m.setTextInteractionFlags(Qt.TextSelectableByMouse)

            lo.addWidget(lbl_m)
            lbl_m_h = _label_height(lbl_m, inner_w, font_size)

        est_h = lbl_m_h + 12

        list_item = QListWidgetItem()
        list_item.setSizeHint(QSize(avail_w, est_h))
        self.chat_list.addItem(list_item)
        self.chat_list.setItemWidget(list_item, item_widget)
        self.chat_list.scrollToBottom()

        def _recalc():
            try:
                item_widget.adjustSize()
                ah = item_widget.sizeHint().height()
                if ah > 10:
                    list_item.setSizeHint(QSize(avail_w, max(est_h, ah + 4)))
            except RuntimeError:
                pass

        QTimer.singleShot(30, _recalc)

        if self.chat_list.count() > 150:
            self.chat_list.takeItem(0)

    def update_viewers(self, count: int):
        self.badge_viewers.setText(f"👁️ {count:,}")


# ── Height helper ─────────────────────────────────────────────────────────────
def _label_height(label: QLabel, width: int, font_size: int) -> int:
    fm   = QFontMetrics(label.font())
    text = label.text()
    if not text:
        return fm.height() + 4

    clean_text = re.sub(r"<[^>]+>", " ", text)
    has_cjk    = any("\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff" for c in clean_text)
    extra      = 4 if has_cjk else 0
    line_h     = fm.height() + extra

    if label.wordWrap():
        h = label.heightForWidth(width)
        if h > 0:
            return h + extra
        char_w = fm.averageCharWidth() or 10
        cpl    = max(1, width // char_w)
        lines  = max(1, (len(clean_text) + cpl - 1) // cpl)
        return line_h * lines + fm.leading() * max(0, lines - 1)
    return line_h


# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    """Aplikasi Utama: Control Panel."""

    def __init__(self):
        super().__init__()
        self.config = config_manager.load_config()
        self.setWindowTitle("🎮 Stream Chat Overlay Manager")
        self.resize(530, 600)

        self.overlay        = None
        self.worker         = None
        self._was_minimized = False

        self.filter_engine = FilterEngine(
            filter_commands=self.config.get("filter_commands", True),
            filter_bad_words=self.config.get("bad_words_filter", True),
            custom_bad_words=self.config.get("custom_bad_words", [])
        )
        self.tts_engine = TTSEngine(
            speed=self.config.get("tts_speed", 170),
            volume=self.config.get("tts_volume", 0.8)
        )
        if self.config.get("tts_enabled", False):
            self.tts_engine.start()

        self._build_ui()
        self.apply_main_theme()

        # ── Timer untuk re-apply interactive state secara periodik ───────
        # Ini adalah safety net jika Windows API state direset oleh OS/DWM
        self._state_timer = QTimer(self)
        self._state_timer.setInterval(3000)          # setiap 3 detik
        self._state_timer.timeout.connect(self._sync_overlay_state)
        self._state_timer.start()

    # ── UI Builder ──────────────────────────────────────────────────────────
    def _build_ui(self):
        self.central_main = QWidget()
        self.central_main.setObjectName("CentralMain")
        self.setCentralWidget(self.central_main)
        root = QVBoxLayout(self.central_main)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        nav = QHBoxLayout()
        self.lbl_mode_title = QLabel("🔗 Hubungkan Live Chat Streaming")
        self.lbl_mode_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        nav.addWidget(self.lbl_mode_title)
        nav.addStretch()
        self.btn_toggle = QPushButton("⚙️ Pengaturan")
        self.btn_toggle.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_toggle.setStyleSheet(
            "background-color:#3B82F6;color:white;padding:6px 14px;border-radius:5px;"
        )
        self.btn_toggle.clicked.connect(self._toggle_mode)
        nav.addWidget(self.btn_toggle)
        root.addLayout(nav)

        self.stack = QStackedWidget()

        # ── Page 1: Link ─────────────────────────────────────────────────
        page1 = QWidget()
        p1    = QVBoxLayout(page1)

        grp = QGroupBox("Metode Koneksi Live Chat")
        gl  = QVBoxLayout(grp)
        self.radio_stream = QRadioButton("Opsi A: Link Streaming (YouTube, Twitch, TikTok)")
        self.radio_chat   = QRadioButton("Opsi B: Link LiveChat (YouTube, Twitch)")
        self.radio_stream.setChecked(True)
        self.input_stream_url = QLineEdit("")
        self.input_stream_url.setPlaceholderText("https://www.youtube.com/watch?v=XXXXX")
        self.input_chat_url = QLineEdit("")
        self.input_chat_url.setPlaceholderText("https://www.youtube.com/live_chat?is_popout=1&v=XXXXX")
        gl.addWidget(self.radio_stream)
        gl.addWidget(self.input_stream_url)
        gl.addWidget(self.radio_chat)
        gl.addWidget(self.input_chat_url)
        p1.addWidget(grp)

        self.lbl_status = QLabel("ℹ️ Masukkan link lalu klik Hubungkan.")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color:#888;font-size:11px;")
        p1.addWidget(self.lbl_status)

        self.btn_connect = QPushButton("🚀 Hubungkan Live Chat Sekarang")
        self.btn_connect.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_connect.setStyleSheet(
            "background-color:#10B981;color:white;padding:10px;border-radius:6px;"
        )
        self.btn_connect.clicked.connect(self._connect_live)
        p1.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("⏹ Stop / Putuskan Koneksi")
        self.btn_disconnect.setFont(QFont("Segoe UI", 9))
        self.btn_disconnect.setStyleSheet(
            "background-color:#EF4444;color:white;padding:8px;border-radius:6px;"
        )
        self.btn_disconnect.clicked.connect(self._disconnect_live)
        self.btn_disconnect.setEnabled(False)
        p1.addWidget(self.btn_disconnect)

        p1.addStretch()
        self.stack.addWidget(page1)

        # ── Page 2: Pengaturan ────────────────────────────────────────────
        page2 = QWidget()
        p2    = QVBoxLayout(page2)

        grp_mt = QGroupBox("Tema Aplikasi Utama")
        gl_mt  = QHBoxLayout(grp_mt)
        gl_mt.addWidget(QLabel("Mode:"))
        self.combo_main_theme = QComboBox()
        self.combo_main_theme.addItems(["Dark", "Light"])
        self.combo_main_theme.setCurrentText(self.config.get("main_theme", "Dark"))
        self.combo_main_theme.currentTextChanged.connect(self._on_main_theme_change)
        gl_mt.addWidget(self.combo_main_theme)
        p2.addWidget(grp_mt)

        grp_ov = QGroupBox("Tampilan Overlay Chat")
        gl_ov  = QVBoxLayout(grp_ov)

        h_theme = QHBoxLayout()
        h_theme.addWidget(QLabel("Tema Overlay:"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems([
            "Dark Neon", "Cyberpunk", "Glassmorphism", "Clean Minimal", "Soft Pastel",
            "Forest Green", "Sunset Orange", "Ocean Blue", "Dark Gold", "Midnight Purple",
        ])
        self.combo_theme.setCurrentText(self.config.get("theme", "Dark Neon"))
        h_theme.addWidget(self.combo_theme)
        gl_ov.addLayout(h_theme)

        h_font = QHBoxLayout()
        h_font.addWidget(QLabel("Ukuran Font Chat:"))
        self.slider_fontsize = QSlider(Qt.Horizontal)
        self.slider_fontsize.setRange(10, 20)
        self.slider_fontsize.setValue(self.config.get("font_size", 13))
        self.lbl_fontsize_val = QLabel(f"{self.config.get('font_size', 13)}px")
        self.lbl_fontsize_val.setFixedWidth(36)
        self.slider_fontsize.valueChanged.connect(
            lambda v: self.lbl_fontsize_val.setText(f"{v}px")
        )
        h_font.addWidget(self.slider_fontsize)
        h_font.addWidget(self.lbl_fontsize_val)
        gl_ov.addLayout(h_font)

        h_opac = QHBoxLayout()
        h_opac.addWidget(QLabel("Transparansi Overlay:"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(20, 100)
        self.slider_opacity.setValue(int(self.config.get("opacity", 0.9) * 100))
        self.slider_opacity.valueChanged.connect(self._on_opacity_change)
        h_opac.addWidget(self.slider_opacity)
        gl_ov.addLayout(h_opac)

        self.chk_click_through = QCheckBox("Click-Through Mode (Tembus Klik Mouse)")
        self.chk_click_through.setChecked(self.config.get("click_through", False))
        gl_ov.addWidget(self.chk_click_through)

        self.chk_show_viewers = QCheckBox("Tampilkan Badge Jumlah Penonton")
        self.chk_show_viewers.setChecked(self.config.get("show_viewer_count", True))
        gl_ov.addWidget(self.chk_show_viewers)
        p2.addWidget(grp_ov)

        grp_adv = QGroupBox("Saringan Chat & TTS Reader")
        gl_adv  = QVBoxLayout(grp_adv)
        self.chk_filter_cmd = QCheckBox("Sembunyikan Perintah Chat (!command)")
        self.chk_filter_cmd.setChecked(self.config.get("filter_commands", True))
        gl_adv.addWidget(self.chk_filter_cmd)
        self.chk_filter_bw = QCheckBox("Filter & Sensor Kata Kasar")
        self.chk_filter_bw.setChecked(self.config.get("bad_words_filter", True))
        gl_adv.addWidget(self.chk_filter_bw)
        self.chk_tts = QCheckBox("Aktifkan Pembaca Chat Suara AI (TTS)")
        self.chk_tts.setChecked(self.config.get("tts_enabled", False))
        gl_adv.addWidget(self.chk_tts)
        p2.addWidget(grp_adv)

        btn_save = QPushButton("💾 Simpan Pengaturan")
        btn_save.setFont(QFont("Segoe UI", 10, QFont.Bold))
        btn_save.setStyleSheet(
            "background-color:#10B981;color:white;padding:10px;border-radius:6px;"
        )
        btn_save.clicked.connect(self._save_settings)
        p2.addWidget(btn_save)

        self.lbl_saved = QLabel("")
        self.lbl_saved.setAlignment(Qt.AlignCenter)
        self.lbl_saved.setStyleSheet("color:#10B981;font-weight:bold;font-size:12px;")
        p2.addWidget(self.lbl_saved)

        p2.addStretch()
        self.stack.addWidget(page2)
        root.addWidget(self.stack)

    # ── Slots ───────────────────────────────────────────────────────────────
    def _toggle_mode(self):
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
            self.lbl_mode_title.setText("⚙️ Pengaturan Overlay")
            self.btn_toggle.setText("🔗 Mode Link Chat")
        else:
            self.stack.setCurrentIndex(0)
            self.lbl_mode_title.setText("🔗 Hubungkan Live Chat Streaming")
            self.btn_toggle.setText("⚙️ Pengaturan")

    def _on_opacity_change(self, val):
        self.config["opacity"] = val / 100.0
        if self.overlay:
            self.overlay.update_config(self.config)

    def _on_main_theme_change(self, text):
        self.config["main_theme"] = text
        self.apply_main_theme()

    def apply_main_theme(self):
        qss = MAIN_APP_STYLES.get(self.config.get("main_theme", "Dark"),
                                   MAIN_APP_STYLES["Dark"])
        self.setStyleSheet(qss)

    def _connect_live(self):
        conn_type = "livechat_url" if self.radio_chat.isChecked() else "stream_url"
        url = (self.input_chat_url.text().strip()
               if conn_type == "livechat_url"
               else self.input_stream_url.text().strip())

        if not url:
            self.lbl_status.setText("⚠️ URL belum diisi.")
            self.lbl_status.setStyleSheet("color:#F59E0B;font-size:11px;")
            return

        self.lbl_status.setText(f"✅ Menghubungkan ke: {url[:55]}...")
        self.lbl_status.setStyleSheet("color:#10B981;font-size:11px;")
        self.config["connection_type"] = conn_type
        config_manager.save_config(self.config)

        if self.worker and self.worker.isRunning():
            self.worker.stop()

        if self.overlay is None:
            self.overlay = OverlayWindow(self.config)
        else:
            self.overlay.chat_list.clear()
            self.overlay.set_pinned("", "")   # reset pinned
            self.overlay.update_config(self.config)
        self.overlay.show()
        self.overlay.raise_()

        self.worker = ChatWorker(
            connection_type=conn_type,
            stream_url=url if conn_type == "stream_url" else "",
            livechat_url=url if conn_type == "livechat_url" else ""
        )
        self.worker.chat_received.connect(self._on_chat)
        self.worker.pinned_chat_received.connect(self._on_pinned)
        self.worker.viewer_count_updated.connect(self._on_viewers)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.status_updated.connect(self._on_worker_status)
        self.worker.start()

        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("🔄 Sedang Menghubungkan...")
        self.btn_disconnect.setEnabled(True)

    def _disconnect_live(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker = None
        if self.overlay:
            self.overlay.hide()
            self.overlay.set_interactive(False)
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("🚀 Hubungkan Live Chat Sekarang")
        self.btn_disconnect.setEnabled(False)
        self.lbl_status.setText("⏹ Koneksi diputus.")
        self.lbl_status.setStyleSheet("color:#888;font-size:11px;")

    def _save_settings(self):
        self.config["theme"]             = self.combo_theme.currentText()
        self.config["main_theme"]        = self.combo_main_theme.currentText()
        self.config["opacity"]           = self.slider_opacity.value() / 100.0
        self.config["font_size"]         = self.slider_fontsize.value()
        self.config["click_through"]     = self.chk_click_through.isChecked()
        self.config["show_viewer_count"] = self.chk_show_viewers.isChecked()
        self.config["filter_commands"]   = self.chk_filter_cmd.isChecked()
        self.config["bad_words_filter"]  = self.chk_filter_bw.isChecked()
        self.config["tts_enabled"]       = self.chk_tts.isChecked()
        config_manager.save_config(self.config)
        if self.overlay:
            self.overlay.update_config(self.config)
        self.apply_main_theme()
        self.filter_engine.filter_commands  = self.config["filter_commands"]
        self.filter_engine.filter_bad_words = self.config["bad_words_filter"]
        if self.config["tts_enabled"]:
            if not self.tts_engine.isRunning():
                self.tts_engine.start()
        else:
            if self.tts_engine.isRunning():
                self.tts_engine.stop()
        self.lbl_saved.setText("✅ Pengaturan berhasil disimpan!")
        QTimer.singleShot(3000, lambda: self.lbl_saved.setText(""))

    def _on_chat(self, author, message, is_superchat, amount, platform):
        try:
            if self.filter_engine.should_ignore(message):
                return
            clean = self.filter_engine.clean_text(message)
            if self.config.get("tts_enabled") and self.tts_engine.isRunning():
                try:
                    tts_text = re.sub(r"<[^>]+>", "", clean)
                    self.tts_engine.speak(author, tts_text)
                except Exception as e:
                    print(f"[MainWindow] Error TTS speak: {e}")
            if self.overlay:
                self.overlay.add_chat(author, clean, is_superchat, amount)
        except Exception as e:
            print(f"[MainWindow] Error _on_chat: {e}")
            if self.overlay:
                self.overlay.add_chat(author, message, is_superchat, amount)

    def _on_pinned(self, author: str, msg: str):
        try:
            if self.overlay:
                self.overlay.set_pinned(author, msg)
        except Exception as e:
            print(f"[MainWindow] Error _on_pinned: {e}")

    def _on_viewers(self, count):
        if self.overlay:
            self.overlay.update_viewers(count)

    def _on_worker_error(self, msg: str):
        self.lbl_status.setText(f"❌ {msg}")
        self.lbl_status.setStyleSheet("color:#EF4444;font-size:11px;")
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("🚀 Hubungkan Live Chat Sekarang")
        self.btn_disconnect.setEnabled(False)

    def _on_worker_status(self, msg: str):
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet("color:#10B981;font-size:11px;")
        # Update button text berdasarkan status koneksi
        if "Live chat terhubung" in msg or "terhubung!" in msg.lower():
            self.btn_connect.setText("✅ Terhubung")
        elif "Menghubungkan" in msg or "Menunggu" in msg:
            self.btn_connect.setText("🔄 Sedang Menghubungkan...")

    # ── Minimize / Restore detection ─────────────────────────────────────────
    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self.overlay:
            # Delay untuk memastikan state Qt sudah stabil
            QTimer.singleShot(150, self._sync_overlay_state)

    def _sync_overlay_state(self):
        """Re-sync overlay interactive state berdasarkan state MainWindow saat ini."""
        if not self.overlay or not self.overlay.isVisible():
            return
        should_be_interactive = not self.isMinimized()
        self._was_minimized   = not should_be_interactive
        self.overlay.set_interactive(should_be_interactive)

    def closeEvent(self, event):
        self._state_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        if self.tts_engine.isRunning():
            self.tts_engine.stop()
        if self.overlay:
            self.overlay.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
