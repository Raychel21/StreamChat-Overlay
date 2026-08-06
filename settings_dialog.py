from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QCheckBox, QSlider, 
                             QPushButton, QSpinBox, QGroupBox)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("⚙️ Pengaturan Stream Chat Overlay")
        self.resize(450, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Group Platform & Channel
        group_platform = QGroupBox("Platform Live Streaming")
        layout_platform = QVBoxLayout(group_platform)
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Platform:"))
        self.combo_platform = QComboBox()
        self.combo_platform.addItems(["Demo", "YouTube", "Twitch", "TikTok"])
        self.combo_platform.setCurrentText(self.config.get("platform", "Demo"))
        h1.addWidget(self.combo_platform)
        layout_platform.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Channel ID / Video ID:"))
        self.input_channel = QLineEdit(self.config.get("channel_id", ""))
        self.input_channel.setPlaceholderText("Masukkan Video ID / Username")
        h2.addWidget(self.input_channel)
        layout_platform.addLayout(h2)

        layout.addWidget(group_platform)

        # 2. Group Tampilan & Overlay
        group_appearance = QGroupBox("Tampilan & Overlay")
        layout_app = QVBoxLayout(group_appearance)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Tema Visual:"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Dark Neon", "Cyberpunk", "Glassmorphism", "Clean Minimal", "Soft Pastel"])
        self.combo_theme.setCurrentText(self.config.get("theme", "Dark Neon"))
        h3.addWidget(self.combo_theme)
        layout_app.addLayout(h3)

        h4 = QHBoxLayout()
        h4.addWidget(QLabel("Transparansi Window:"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(30, 100)
        self.slider_opacity.setValue(int(self.config.get("opacity", 0.9) * 100))
        h4.addWidget(self.slider_opacity)
        layout_app.addLayout(h4)

        self.chk_always_top = QCheckBox("Window Selalu di Atas (Always on Top)")
        self.chk_always_top.setChecked(self.config.get("always_on_top", True))
        layout_app.addWidget(self.chk_always_top)

        self.chk_click_through = QCheckBox("Click-Through Mode (Mouse Passthrough/Tembus Klik)")
        self.chk_click_through.setChecked(self.config.get("click_through", False))
        layout_app.addWidget(self.chk_click_through)

        self.chk_show_viewers = QCheckBox("Tampilkan Jumlah Penonton (Live Viewers Badge)")
        self.chk_show_viewers.setChecked(self.config.get("show_viewer_count", True))
        layout_app.addWidget(self.chk_show_viewers)

        layout.addWidget(group_appearance)

        # 3. Group Fitur Advance & Text-To-Speech (TTS)
        group_advance = QGroupBox("Saringan Chat & TTS Voice Reader")
        layout_adv = QVBoxLayout(group_advance)

        self.chk_filter_cmd = QCheckBox("Sembunyikan Perintah Chat (!command)")
        self.chk_filter_cmd.setChecked(self.config.get("filter_commands", True))
        layout_adv.addWidget(self.chk_filter_cmd)

        self.chk_filter_badwords = QCheckBox("Filter & Sensor Kata Kasar (Bad Words)")
        self.chk_filter_badwords.setChecked(self.config.get("bad_words_filter", True))
        layout_adv.addWidget(self.chk_filter_badwords)

        self.chk_tts = QCheckBox("Aktifkan Suara Pembaca Chat (Text-To-Speech)")
        self.chk_tts.setChecked(self.config.get("tts_enabled", False))
        layout_adv.addWidget(self.chk_tts)

        layout.addWidget(group_advance)

        # Button Save / Cancel
        h_btn = QHBoxLayout()
        btn_save = QPushButton("Simpan Pengaturan")
        btn_save.setStyleSheet("background-color: #00C9A7; color: white; font-weight: bold; padding: 8px; border-radius: 6px;")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Batal")
        btn_cancel.clicked.connect(self.reject)
        h_btn.addWidget(btn_save)
        h_btn.addWidget(btn_cancel)

        layout.addLayout(h_btn)

    def get_updated_config(self):
        self.config["platform"] = self.combo_platform.currentText()
        self.config["channel_id"] = self.input_channel.text()
        self.config["theme"] = self.combo_theme.currentText()
        self.config["opacity"] = self.slider_opacity.value() / 100.0
        self.config["always_on_top"] = self.chk_always_top.isChecked()
        self.config["click_through"] = self.chk_click_through.isChecked()
        self.config["show_viewer_count"] = self.chk_show_viewers.isChecked()
        self.config["filter_commands"] = self.chk_filter_cmd.isChecked()
        self.config["bad_words_filter"] = self.chk_filter_badwords.isChecked()
        self.config["tts_enabled"] = self.chk_tts.isChecked()
        return self.config
