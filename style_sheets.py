import re

# Theme QSS stylesheets for Stream Chat Overlay & Main Application
#
# PENTING: QListWidget::item TIDAK menggunakan padding QSS karena akan
# menyebabkan height dari setSizeHint() tidak akurat → teks terpotong.
# Semua padding/margin ditangani oleh QVBoxLayout di dalam widget item.

def get_theme_qss(theme_name: str, opacity: float = 0.9) -> str:
    """
    Mengambil QSS tema dengan transparansi dinamis HANYA pada background
    (Overlay window background & chat item background).
    Teks, font, badge, border, dan gambar emote tetap 100% solid (tidak pudar).
    """
    base_qss = THEMES.get(theme_name, THEMES.get("Dark Neon", ""))
    opacity = max(0.05, min(1.0, opacity))

    def replace_rgba(match):
        prefix = match.group(1)
        r, g, b = match.group(2), match.group(3), match.group(4)
        alpha_str = match.group(5)
        try:
            alpha_val = float(alpha_str)
            if alpha_val > 1.0:
                new_alpha = max(0, min(255, int(alpha_val * opacity)))
                return f"{prefix}rgba({r}, {g}, {b}, {new_alpha})"
            else:
                new_alpha = round(max(0.0, min(1.0, alpha_val * opacity)), 3)
                return f"{prefix}rgba({r}, {g}, {b}, {new_alpha})"
        except ValueError:
            return match.group(0)

    pattern = r'(background(?:-color)?\s*:\s*)rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)'
    return re.sub(pattern, replace_rgba, base_qss)

THEMES = {
    "Dark Neon": """
        QWidget#CentralWidget {
            background-color: rgba(18, 18, 24, 215);
            border-radius: 12px;
            border: 1px solid rgba(0, 242, 254, 0.4);
        }
        QLabel {
            color: #E0E0E0;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }
        QListWidget {
            background: transparent;
            border: none;
            outline: none;
        }
        QListWidget::item {
            background: rgba(30, 30, 42, 170);
            border-radius: 8px;
            margin: 2px 4px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        QListWidget::item:hover {
            background: rgba(40, 40, 60, 200);
            border: 1px solid rgba(0, 242, 254, 0.5);
        }
        QScrollBar:vertical {
            background: rgba(255, 255, 255, 0.05);
            width: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 242, 254, 0.4);
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        #HeaderBar {
            background: rgba(10, 10, 15, 225);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border-bottom: 1px solid rgba(0, 242, 254, 0.3);
        }
        #ViewerBadge {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FF007F, stop:1 #7928CA);
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }
        #PinnedContainer {
            background: rgba(255, 215, 0, 0.10);
            border-left: 3px solid #FFD700;
            border-bottom: 1px solid rgba(255, 215, 0, 0.25);
        }
        #PinLabel {
            color: #FFD700;
            font-size: 8pt;
        }
        #PinnedMessage {
            color: #FFFFFF;
        }
        #PinnedDivider {
            color: rgba(0, 242, 254, 0.2);
        }
    """,

    "Cyberpunk": """
        QWidget#CentralWidget {
            background-color: rgba(15, 15, 26, 230);
            border-radius: 10px;
            border: 2px solid #FCEE0A;
        }
        QLabel {
            color: #00F0FF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }
        QListWidget {
            background: transparent;
            border: none;
            outline: none;
        }
        QListWidget::item {
            background: rgba(254, 0, 184, 0.12);
            border-left: 3px solid #00F0FF;
            border-radius: 4px;
            margin: 2px 4px;
        }
        QListWidget::item:hover {
            background: rgba(254, 0, 184, 0.22);
        }
        QScrollBar:vertical {
            background: rgba(255, 255, 255, 0.05);
            width: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 240, 255, 0.5);
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        #HeaderBar {
            background: #00F0FF;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        #HeaderBar QLabel {
            color: #05050A;
            font-weight: bold;
        }
        #ViewerBadge {
            background: #FCEE0A;
            color: #000000;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }
        #PinnedContainer {
            background: rgba(252, 238, 10, 0.10);
            border-left: 3px solid #FCEE0A;
            border-bottom: 1px solid rgba(252, 238, 10, 0.25);
        }
        #PinLabel {
            color: #FCEE0A;
            font-size: 8pt;
        }
        #PinnedMessage {
            color: #00F0FF;
        }
        #PinnedDivider {
            color: rgba(252, 238, 10, 0.3);
        }
    """,

    "Glassmorphism": """
        QWidget#CentralWidget {
            background-color: rgba(255, 255, 255, 28);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.25);
        }
        QLabel {
            color: #FFFFFF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }
        QListWidget {
            background: transparent;
            border: none;
            outline: none;
        }
        QListWidget::item {
            background: rgba(255, 255, 255, 0.14);
            border-radius: 10px;
            margin: 2px 4px;
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        QListWidget::item:hover {
            background: rgba(255, 255, 255, 0.22);
        }
        QScrollBar:vertical {
            background: rgba(255, 255, 255, 0.08);
            width: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.4);
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        #HeaderBar {
            background: rgba(255, 255, 255, 0.18);
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        }
        #ViewerBadge {
            background: rgba(0, 201, 167, 0.85);
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }
        #PinnedContainer {
            background: rgba(255, 255, 255, 0.12);
            border-left: 3px solid rgba(0, 201, 167, 0.9);
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        }
        #PinLabel {
            color: rgba(0, 201, 167, 1);
            font-size: 8pt;
        }
        #PinnedMessage {
            color: #FFFFFF;
        }
        #PinnedDivider {
            color: rgba(255, 255, 255, 0.2);
        }
    """,

    "Clean Minimal": """
        QWidget#CentralWidget {
            background-color: rgba(20, 20, 20, 215);
            border-radius: 8px;
            border: 1px solid #444444;
        }
        QLabel {
            color: #FFFFFF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }
        QListWidget {
            background: transparent;
            border: none;
        }
        QListWidget::item {
            background: rgba(40, 40, 40, 185);
            border-radius: 6px;
            margin: 2px 4px;
        }
        QListWidget::item:hover {
            background: rgba(60, 60, 60, 200);
        }
        QScrollBar:vertical {
            background: rgba(255, 255, 255, 0.06);
            width: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.35);
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        #HeaderBar {
            background: rgba(30, 30, 30, 245);
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        #ViewerBadge {
            background: #E50914;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 3px 10px;
        }
        #PinnedContainer {
            background: rgba(255, 255, 255, 0.06);
            border-left: 3px solid #E50914;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        #PinLabel {
            color: #E50914;
            font-size: 8pt;
        }
        #PinnedMessage {
            color: #DDDDDD;
        }
        #PinnedDivider {
            color: rgba(255, 255, 255, 0.15);
        }
    """,

    "Soft Pastel": """
        QWidget#CentralWidget {
            background-color: rgba(40, 30, 50, 225);
            border-radius: 14px;
            border: 1px solid #FFC6FF;
        }
        QLabel {
            color: #FDFFB6;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }
        QListWidget {
            background: transparent;
            border: none;
        }
        QListWidget::item {
            background: rgba(80, 60, 100, 175);
            border-radius: 10px;
            margin: 2px 4px;
            border: 1px solid rgba(255, 198, 255, 0.25);
        }
        QListWidget::item:hover {
            background: rgba(100, 80, 130, 200);
            border: 1px solid rgba(255, 198, 255, 0.5);
        }
        QScrollBar:vertical {
            background: rgba(255, 255, 255, 0.07);
            width: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background: rgba(255, 198, 255, 0.5);
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        #HeaderBar {
            background: rgba(60, 40, 80, 245);
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
        }
        #ViewerBadge {
            background: #FFADAD;
            color: #4A0E17;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }
        #PinnedContainer {
            background: rgba(255, 198, 255, 0.10);
            border-left: 3px solid #FFC6FF;
            border-bottom: 1px solid rgba(255, 198, 255, 0.2);
        }
        #PinLabel {
            color: #FFC6FF;
            font-size: 8pt;
        }
        #PinnedMessage {
            color: #FDFFB6;
        }
        #PinnedDivider {
            color: rgba(255, 198, 255, 0.25);
        }
    """
}

MAIN_APP_STYLES = {
    "Dark": """
        QMainWindow, QWidget#CentralMain {
            background-color: #121212;
            color: #FFFFFF;
        }
        QLabel {
            color: #E0E0E0;
            font-family: 'Segoe UI', Arial;
        }
        QGroupBox {
            color: #00F0FF;
            font-weight: bold;
            border: 1px solid #333333;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #1E1E1E;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QLineEdit {
            background-color: #2D2D2D;
            color: #FFFFFF;
            border: 1px solid #444444;
            border-radius: 5px;
            padding: 6px;
        }
        QLineEdit:focus {
            border: 1px solid #00F0FF;
        }
        QComboBox {
            background-color: #2D2D2D;
            color: #FFFFFF;
            border: 1px solid #444444;
            border-radius: 5px;
            padding: 5px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #2D2D2D;
            color: #FFFFFF;
            selection-background-color: #3B82F6;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #333;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #00F0FF;
            width: 14px;
            height: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QCheckBox, QRadioButton {
            color: #DDDDDD;
        }
        QPushButton {
            border-radius: 6px;
        }
    """,

    "Light": """
        QMainWindow, QWidget#CentralMain {
            background-color: #F8FAFC;
            color: #0F172A;
        }
        QLabel {
            color: #1E293B;
            font-family: 'Segoe UI', Arial;
        }
        QGroupBox {
            color: #2563EB;
            font-weight: bold;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #FFFFFF;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QLineEdit {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 5px;
            padding: 6px;
        }
        QLineEdit:focus {
            border: 1px solid #2563EB;
        }
        QComboBox {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 5px;
            padding: 5px;
        }
        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #0F172A;
            selection-background-color: #DBEAFE;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #CBD5E1;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #2563EB;
            width: 14px;
            height: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QCheckBox, QRadioButton {
            color: #334155;
        }
        QPushButton {
            border-radius: 6px;
        }
    """
}
