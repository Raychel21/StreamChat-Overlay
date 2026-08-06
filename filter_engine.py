import re

DEFAULT_BAD_WORDS = [
    "anjing", "babi", "kuntul", "kontol", "memek", "jembut", "goblok", "tolol",
    "bangsat", "pantek", "fuck", "shit", "bitch", "asshole", "bastard"
]

class FilterEngine:
    def __init__(self, filter_commands=True, filter_bad_words=True, custom_bad_words=None):
        self.filter_commands = filter_commands
        self.filter_bad_words = filter_bad_words
        self.bad_words = set(DEFAULT_BAD_WORDS)
        if custom_bad_words:
            self.bad_words.update([w.lower().strip() for w in custom_bad_words if w.strip()])

    def should_ignore(self, message):
        """Memeriksa apakah pesan harus diabaikan (misal: command !cmd)."""
        if not message:
            return True
        text = message.strip()
        if self.filter_commands and text.startswith("!"):
            return True
        return False

    def clean_text(self, text):
        """Sensor kata-kata kasar dengan ***."""
        if not self.filter_bad_words or not text:
            return text
        
        words = text.split()
        cleaned_words = []
        for word in words:
            # Hilangkan tanda baca untuk cek kata
            clean_word = re.sub(r'[^\w\s]', '', word).lower()
            if clean_word in self.bad_words:
                cleaned_words.append("*" * len(word))
            else:
                cleaned_words.append(word)
        return " ".join(cleaned_words)
