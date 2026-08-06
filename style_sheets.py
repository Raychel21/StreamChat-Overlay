import re

# Theme QSS stylesheets for Stream Chat Overlay & Main Application
#
# PENTING: QListWidget::item TIDAK menggunakan padding QSS karena akan
# menyebabkan height dari setSizeHint() tidak akurat → teks terpotong.
# Semua padding/margin ditangani oleh QVBoxLayout di dalam widget item.
# Font options (10 unique font styles for overlay chat)
DEFAULT_THEME_FONTS = {
    "Dark Neon": "Segoe UI",
    "Cyberpunk": "Consolas",
    "Glassmorphism": "Century Gothic",
    "Clean Minimal": "Trebuchet MS",
    "Soft Pastel": "Comic Sans MS",
    "Forest Green": "Georgia",
    "Sunset Orange": "Verdana",
    "Ocean Blue": "Bahnschrift",
    "Dark Gold": "Palatino Linotype",
    "Midnight Purple": "Cascadia Code",
}

FONT_OPTIONS = [
    "Segoe UI",
    "Consolas",
    "Comic Sans MS",
    "Trebuchet MS",
    "Century Gothic",
    "Georgia",
    "Verdana",
    "Bahnschrift",
    "Palatino Linotype",
    "Cascadia Code",
]

def get_theme_qss(theme_name: str, overlay_opacity: float = 0.9, chat_opacity: float = 0.9, font_family: str = None) -> str:
    """
    Mengambil QSS tema dengan dua kontrol transparansi terpisah dan font family dinamis:
    - overlay_opacity : transparansi background window overlay (CentralWidget & HeaderBar)
    - chat_opacity    : transparansi background item chat (QListWidget::item)
    - font_family     : jenis font khusus (jika None, gunakan font bawaan tema)
    Teks, font, badge, border, dan gambar emote tetap 100% solid (tidak pudar).
    """
    base_qss = THEMES.get(theme_name, THEMES.get("Dark Neon", ""))
    overlay_opacity = max(0.05, min(1.0, overlay_opacity))
    chat_opacity    = max(0.05, min(1.0, chat_opacity))

    selected_font = font_family or DEFAULT_THEME_FONTS.get(theme_name, "Segoe UI")

    # Replace font-family di QSS
    font_pattern = r'font-family:\s*[^;]+;'
    new_font_decl = f"font-family: '{selected_font}', 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;"
    base_qss = re.sub(font_pattern, new_font_decl, base_qss)

    def replace_rgba(match):
        prefix    = match.group(1)
        r, g, b   = match.group(2), match.group(3), match.group(4)
        alpha_str = match.group(5)
        tag       = match.group(6)          # "OVERLAY" or "CHAT"
        try:
            alpha_val = float(alpha_str)
            op = overlay_opacity if tag == "OVERLAY" else chat_opacity
            if alpha_val > 1.0:
                new_alpha = max(0, min(255, int(alpha_val * op)))
            else:
                new_alpha = round(max(0.0, min(1.0, alpha_val * op)), 3)
            return f"{prefix}rgba({r}, {g}, {b}, {new_alpha})"
        except ValueError:
            return match.group(0)

    # Tag format: rgba(r,g,b,a)/*OVERLAY*/ or rgba(r,g,b,a)/*CHAT*/
    pattern = (r'(background(?:-color)?\s*:\s*)'
               r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)'
               r'/\*(OVERLAY|CHAT)\*/')
    result = re.sub(pattern, replace_rgba, base_qss)
    return result


# ─── Tag helper ──────────────────────────────────────────────────────────────
def _O(r, g, b, a):
    """Return rgba string tagged as OVERLAY background."""
    return f"rgba({r}, {g}, {b}, {a})/*OVERLAY*/"

def _C(r, g, b, a):
    """Return rgba string tagged as CHAT item background."""
    return f"rgba({r}, {g}, {b}, {a})/*CHAT*/"


# ─────────────────────────────────────────────────────────────────────────────
# IMPORTANT: rgba values that should react to opacity sliders MUST use the
# _O() or _C() helpers. Static colors (borders, text, badges) use plain rgba().
# ─────────────────────────────────────────────────────────────────────────────

def _build_themes():
    T = {}

    # ── Dark Neon ─────────────────────────────────────────────────────────────
    T["Dark Neon"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(18, 18, 24, 215)};
            border-radius: 12px;
            border: 1px solid rgba(0, 242, 254, 0.4);
        }}
        QLabel {{
            color: #E0E0E0;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(30, 30, 42, 170)};
            border-radius: 8px;
            margin: 2px 4px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        QListWidget::item:hover {{
            background: {_C(40, 40, 60, 200)};
            border: 1px solid rgba(0, 242, 254, 0.5);
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.05);
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0, 242, 254, 0.4);
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: {_O(10, 10, 15, 225)};
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border-bottom: 1px solid rgba(0, 242, 254, 0.3);
        }}
        #ViewerBadge {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FF007F, stop:1 #7928CA);
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(255, 215, 0, 0.10);
            border-left: 3px solid #FFD700;
            border-bottom: 1px solid rgba(255, 215, 0, 0.25);
        }}
        #PinLabel {{
            color: #FFD700;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #FFFFFF;
        }}
        #PinnedDivider {{
            color: rgba(0, 242, 254, 0.2);
        }}
    """

    # ── Cyberpunk ─────────────────────────────────────────────────────────────
    T["Cyberpunk"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(15, 15, 26, 230)};
            border-radius: 10px;
            border: 2px solid #FCEE0A;
        }}
        QLabel {{
            color: #00F0FF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(254, 0, 184, 30)};
            border-left: 3px solid #00F0FF;
            border-radius: 4px;
            margin: 2px 4px;
        }}
        QListWidget::item:hover {{
            background: {_C(254, 0, 184, 56)};
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.05);
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0, 240, 255, 0.5);
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: #00F0FF;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
        #HeaderBar QLabel {{
            color: #05050A;
            font-weight: bold;
        }}
        #ViewerBadge {{
            background: #FCEE0A;
            color: #000000;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(252, 238, 10, 0.10);
            border-left: 3px solid #FCEE0A;
            border-bottom: 1px solid rgba(252, 238, 10, 0.25);
        }}
        #PinLabel {{
            color: #FCEE0A;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #00F0FF;
        }}
        #PinnedDivider {{
            color: rgba(252, 238, 10, 0.3);
        }}
    """

    # ── Glassmorphism ─────────────────────────────────────────────────────────
    T["Glassmorphism"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(255, 255, 255, 28)};
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.25);
        }}
        QLabel {{
            color: #FFFFFF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(255, 255, 255, 35)};
            border-radius: 10px;
            margin: 2px 4px;
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        QListWidget::item:hover {{
            background: {_C(255, 255, 255, 56)};
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.08);
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.4);
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: {_O(255, 255, 255, 46)};
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        }}
        #ViewerBadge {{
            background: rgba(0, 201, 167, 0.85);
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(255, 255, 255, 0.12);
            border-left: 3px solid rgba(0, 201, 167, 0.9);
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        }}
        #PinLabel {{
            color: rgba(0, 201, 167, 1);
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #FFFFFF;
        }}
        #PinnedDivider {{
            color: rgba(255, 255, 255, 0.2);
        }}
    """

    # ── Clean Minimal ─────────────────────────────────────────────────────────
    T["Clean Minimal"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(20, 20, 20, 215)};
            border-radius: 8px;
            border: 1px solid #444444;
        }}
        QLabel {{
            color: #FFFFFF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
        }}
        QListWidget::item {{
            background: {_C(40, 40, 40, 185)};
            border-radius: 6px;
            margin: 2px 4px;
        }}
        QListWidget::item:hover {{
            background: {_C(60, 60, 60, 200)};
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.06);
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.35);
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: {_O(30, 30, 30, 245)};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
        #ViewerBadge {{
            background: #E50914;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(255, 255, 255, 0.06);
            border-left: 3px solid #E50914;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        #PinLabel {{
            color: #E50914;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #DDDDDD;
        }}
        #PinnedDivider {{
            color: rgba(255, 255, 255, 0.15);
        }}
    """

    # ── Soft Pastel ───────────────────────────────────────────────────────────
    T["Soft Pastel"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(40, 30, 50, 225)};
            border-radius: 14px;
            border: 1px solid #FFC6FF;
        }}
        QLabel {{
            color: #FDFFB6;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
        }}
        QListWidget::item {{
            background: {_C(80, 60, 100, 175)};
            border-radius: 10px;
            margin: 2px 4px;
            border: 1px solid rgba(255, 198, 255, 0.25);
        }}
        QListWidget::item:hover {{
            background: {_C(100, 80, 130, 200)};
            border: 1px solid rgba(255, 198, 255, 0.5);
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.07);
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 198, 255, 0.5);
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: {_O(60, 40, 80, 245)};
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
        }}
        #ViewerBadge {{
            background: #FFADAD;
            color: #4A0E17;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(255, 198, 255, 0.10);
            border-left: 3px solid #FFC6FF;
            border-bottom: 1px solid rgba(255, 198, 255, 0.2);
        }}
        #PinLabel {{
            color: #FFC6FF;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #FDFFB6;
        }}
        #PinnedDivider {{
            color: rgba(255, 198, 255, 0.25);
        }}
    """

    # ── Forest Green ──────────────────────────────────────────────────────────
    # Multi-color: Hijau Tua (#0B5E1A) → Emerald (#1DB954) → Neon (#39FF14) → Lime (#C8FF00) → Kuning Chartreuse (#AAFF00)
    # Pola: kanopi hutan dari kedalaman gelap menuju cahaya lime matahari,
    # seperti melihat ke atas dari dalam hutan. Header diagonal, scrollbar vertikal gelap→terang.
    T["Forest Green"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(5, 16, 7, 225)};
            border-radius: 10px;
            border: 1px solid rgba(57, 255, 20, 0.5);
        }}
        QLabel {{
            color: #D0FFCC;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(7, 46, 13, 185)};
            border-left: 3px solid #39FF14;
            border-radius: 5px;
            margin: 2px 4px;
            border-top: 1px solid rgba(29, 185, 84, 0.15);
            border-right: 1px solid rgba(170, 255, 0, 0.06);
            border-bottom: 2px solid rgba(200, 255, 0, 0.22);
        }}
        QListWidget::item:hover {{
            background: {_C(10, 70, 20, 218)};
            border-left: 3px solid #C8FF00;
            border-top: 1px solid rgba(57, 255, 20, 0.3);
            border-bottom: 2px solid rgba(200, 255, 0, 0.5);
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.04);
            width: 5px;
            border-radius: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0B5E1A, stop:0.45 #39FF14, stop:1 #C8FF00);
            border-radius: 2px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0    #0B5E1A,
                stop:0.28 #1DB954,
                stop:0.56 #39FF14,
                stop:0.78 #C8FF00,
                stop:1    #AAFF00);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 3px solid rgba(200, 255, 0, 0.9);
        }}
        #HeaderBar QLabel {{
            color: #071A08;
            font-weight: bold;
        }}
        #ViewerBadge {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0B5E1A, stop:1 #39FF14);
            color: #EFFFEE;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(57, 255, 20, 0.07);
            border-left: 3px solid #39FF14;
            border-bottom: 1px solid rgba(200, 255, 0, 0.22);
        }}
        #PinLabel {{
            color: #C8FF00;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #D0FFCC;
        }}
        #PinnedDivider {{
            color: rgba(57, 255, 20, 0.25);
        }}
    """

    # ── Sunset Orange ─────────────────────────────────────────────────────────
    # Multi-color: Merah Lava (#C0392B) → Magenta (#FF0090) → Oranye (#FF6B00) → Emas (#FFB300)
    # Header gradient panjang 4 warna seperti langit senja dramatis,
    # item berlapis warna warm ember, scrollbar tricolor orange-pink.
    T["Sunset Orange"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(18, 5, 2, 225)};
            border-radius: 10px;
            border: 1px solid rgba(255, 107, 0, 0.6);
        }}
        QLabel {{
            color: #FFE8C8;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(95, 22, 4, 185)};
            border-left: 3px solid #FF6B00;
            border-radius: 5px;
            margin: 2px 4px;
            border-top: 1px solid rgba(255, 179, 0, 0.12);
            border-right: 1px solid rgba(192, 57, 43, 0.08);
            border-bottom: 2px solid rgba(255, 0, 144, 0.28);
        }}
        QListWidget::item:hover {{
            background: {_C(140, 35, 8, 218)};
            border-left: 3px solid #FF0090;
            border-top: 1px solid rgba(255, 179, 0, 0.3);
            border-bottom: 2px solid rgba(255, 0, 144, 0.65);
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.04);
            width: 5px;
            border-radius: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF0090, stop:0.5 #FF6B00, stop:1 #FFB300);
            border-radius: 2px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0    #C0392B,
                stop:0.3  #FF0090,
                stop:0.6  #FF6B00,
                stop:0.85 #FF9500,
                stop:1    #FFB300);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 3px solid rgba(255, 0, 144, 0.85);
        }}
        #HeaderBar QLabel {{
            color: #FFF5E8;
            font-weight: bold;
        }}
        #ViewerBadge {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #C0392B, stop:1 #FF0090);
            color: #FFFFFF;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(255, 107, 0, 0.09);
            border-left: 3px solid #FF6B00;
            border-bottom: 1px solid rgba(255, 0, 144, 0.22);
        }}
        #PinLabel {{
            color: #FFB300;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #FFE8C8;
        }}
        #PinnedDivider {{
            color: rgba(255, 107, 0, 0.22);
        }}
    """

    # ── Ocean Blue ────────────────────────────────────────────────────────────
    # Multi-color: Navy (#003875) → Royal (#0052CC) → Cyan (#00CFFF) → Teal (#00FFC8) → Aqua (#00FFE5)
    # Pola: permukaan laut dari kedalaman gelap ke cahaya permukaan berkilau.
    # Header diagonal dari biru navy gelap ke aquamarine terang, scrollbar vertikal deep→aqua.
    T["Ocean Blue"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(2, 8, 30, 225)};
            border-radius: 12px;
            border: 1px solid rgba(0, 207, 255, 0.5);
        }}
        QLabel {{
            color: #C8F5FF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(3, 28, 75, 185)};
            border-left: 3px solid #00CFFF;
            border-radius: 5px;
            margin: 2px 4px;
            border-top: 1px solid rgba(0, 82, 204, 0.2);
            border-right: 1px solid rgba(0, 255, 229, 0.05);
            border-bottom: 2px solid rgba(0, 255, 200, 0.22);
        }}
        QListWidget::item:hover {{
            background: {_C(4, 45, 110, 218)};
            border-left: 3px solid #00FFC8;
            border-top: 1px solid rgba(0, 207, 255, 0.3);
            border-bottom: 2px solid rgba(0, 255, 200, 0.55);
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.04);
            width: 5px;
            border-radius: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #003875, stop:0.45 #00CFFF, stop:1 #00FFE5);
            border-radius: 2px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0    #003875,
                stop:0.28 #0052CC,
                stop:0.56 #00CFFF,
                stop:0.78 #00FFC8,
                stop:1    #00FFE5);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border-bottom: 3px solid rgba(0, 255, 200, 0.9);
        }}
        #HeaderBar QLabel {{
            color: #FFFFFF;
            font-weight: bold;
        }}
        #ViewerBadge {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #003875, stop:1 #00CFFF);
            color: #EAFAFF;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(0, 207, 255, 0.07);
            border-left: 3px solid #00CFFF;
            border-bottom: 1px solid rgba(0, 255, 200, 0.22);
        }}
        #PinLabel {{
            color: #00FFC8;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #C8F5FF;
        }}
        #PinnedDivider {{
            color: rgba(0, 207, 255, 0.2);
        }}
    """

    # ── Dark Gold ─────────────────────────────────────────────────────────────
    # Multi-color: Onyx Gelap (#120D04) → Bronz Royal (#4A3A14) → Emas Klasik (#9E7D2B) → Emas 24K (#D4AF37) → Champagne Sheen (#FFE485)
    # Pola: perpaduan kemewahan hitam onyx gelap & kilau emas murni yang sangat elegan.
    # Header diagonal onyx-ke-champagne gold, item obsidian gelap dengan border emas 24K berkilau.
    T["Dark Gold"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(12, 9, 4, 230)};
            border-radius: 10px;
            border: 1px solid rgba(212, 175, 55, 0.65);
        }}
        QLabel {{
            color: #FFFDF0;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(26, 20, 10, 190)};
            border-left: 3px solid #D4AF37;
            border-radius: 5px;
            margin: 2px 4px;
            border-top: 1px solid rgba(255, 230, 150, 0.18);
            border-right: 1px solid rgba(212, 175, 55, 0.08);
            border-bottom: 2px solid rgba(160, 120, 30, 0.35);
        }}
        QListWidget::item:hover {{
            background: {_C(44, 34, 16, 220)};
            border-left: 3px solid #FFD700;
            border-top: 1px solid rgba(255, 240, 180, 0.35);
            border-bottom: 2px solid rgba(255, 215, 0, 0.65);
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.04);
            width: 5px;
            border-radius: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #33260C, stop:0.5 #D4AF37, stop:1 #FFE485);
            border-radius: 2px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0    #120D04,
                stop:0.3  #4A3A14,
                stop:0.6  #9E7D2B,
                stop:0.85 #D4AF37,
                stop:1    #FFE485);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 3px solid #D4AF37;
        }}
        #HeaderBar QLabel {{
            color: #FFFFFF;
            font-weight: bold;
        }}
        #ViewerBadge {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4A3A14, stop:1 #D4AF37);
            color: #0D0903;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(212, 175, 55, 0.08);
            border-left: 3px solid #FFD700;
            border-bottom: 1px solid rgba(255, 215, 0, 0.25);
        }}
        #PinLabel {{
            color: #FFD700;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #FFFDF0;
        }}
        #PinnedDivider {{
            color: rgba(212, 175, 55, 0.28);
        }}
    """

    # ── Midnight Purple ───────────────────────────────────────────────────────
    # Multi-color: Hitam Ruang (#0D0020) → Indigo (#3D0080) → Violet (#8B00FF) → Hot Pink (#CC0066) → Neon Rose (#FF2D78)
    # Pola: nebula galaksi — dari kegelapan ruang angkasa meledak ke warna pink neon supernova.
    # Header diagonal kiri gelap ke kanan neon, scrollbar vertikal dari ungu tua ke rose neon.
    T["Midnight Purple"] = f"""
        QWidget#CentralWidget {{
            background-color: {_O(7, 2, 22, 228)};
            border-radius: 12px;
            border: 1px solid rgba(139, 0, 255, 0.55);
        }}
        QLabel {{
            color: #EEE5FF;
            font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif;
            line-height: 1.4;
        }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {_C(42, 8, 100, 185)};
            border-left: 3px solid #8B00FF;
            border-radius: 5px;
            margin: 2px 4px;
            border-top: 1px solid rgba(61, 0, 128, 0.2);
            border-right: 1px solid rgba(255, 45, 120, 0.05);
            border-bottom: 2px solid rgba(255, 45, 120, 0.22);
        }}
        QListWidget::item:hover {{
            background: {_C(62, 12, 142, 218)};
            border-left: 3px solid #FF2D78;
            border-top: 1px solid rgba(139, 0, 255, 0.3);
            border-bottom: 2px solid rgba(255, 45, 120, 0.6);
        }}
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.04);
            width: 5px;
            border-radius: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0D0020, stop:0.45 #8B00FF, stop:1 #FF2D78);
            border-radius: 2px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        #HeaderBar {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0    #0D0020,
                stop:0.28 #3D0080,
                stop:0.56 #8B00FF,
                stop:0.78 #CC0066,
                stop:1    #FF2D78);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border-bottom: 3px solid rgba(255, 45, 120, 0.9);
        }}
        #HeaderBar QLabel {{
            color: #FFF0FF;
            font-weight: bold;
        }}
        #ViewerBadge {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3D0080, stop:1 #8B00FF);
            color: #FFFFFF;
            font-weight: bold;
            border-radius: 10px;
            padding: 3px 10px;
        }}
        #PinnedContainer {{
            background: rgba(139, 0, 255, 0.08);
            border-left: 3px solid #8B00FF;
            border-bottom: 1px solid rgba(255, 45, 120, 0.2);
        }}
        #PinLabel {{
            color: #FF2D78;
            font-size: 8pt;
        }}
        #PinnedMessage {{
            color: #EEE5FF;
        }}
        #PinnedDivider {{
            color: rgba(139, 0, 255, 0.25);
        }}
    """

    return T

THEMES = _build_themes()



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
