import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "connection_type": "stream_url",  # stream_url ATAU livechat_url
    "stream_url": "",
    "livechat_url": "",
    "theme": "Dark Neon",
    "main_theme": "Dark", # Dark ATAU Light mode untuk Aplikasi Utama
    "always_on_top": True,
    "opacity": 0.9,
    "click_through": False,
    "font_size": 13,
    "tts_enabled": False,
    "tts_speed": 170,
    "tts_volume": 0.8,
    "filter_commands": True,
    "bad_words_filter": True,
    "custom_bad_words": ["badword1", "badword2"],
    "show_viewer_count": True
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Error saving config:", e)
