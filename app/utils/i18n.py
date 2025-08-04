import yaml
from pathlib import Path
from typing import Dict, List

LANG_DIR = Path(__file__).parent.parent / "lang"

class Translator:
    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {}
        self.available_languages: List[str] = []
        self._load_translations()

    def _load_translations(self):
        for lang_file in LANG_DIR.glob("*.yaml"):
            lang_code = lang_file.stem
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations[lang_code] = yaml.safe_load(f)
            self.available_languages.append(lang_code)

    def get_translator(self, lang_code: str = "en"):
        # Fallback to English if the language or a specific key is missing
        if lang_code not in self.translations:
            lang_code = "en"

        def translate(key: str) -> str:
            return self.translations.get(lang_code, {}).get(key, self.translations.get("en", {}).get(key, key))

        return translate

# Global instance
translator = Translator()