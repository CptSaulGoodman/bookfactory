import logging
from fastapi import Request, Header
from app.utils.i18n import translator

logging.basicConfig(level=logging.INFO)
current_language = "en"

def get_language(request: Request, accept_language: str = Header(None)) -> str:
    # 1. Check for language cookie
    lang_code = request.cookies.get("language")
    logging.info(f"Checking for language cookie: {lang_code}")
    if lang_code and lang_code in translator.available_languages:
        logging.info(f"Language '{lang_code}' from cookie is valid.")
        set_current_language(lang_code)
        return lang_code

    # 2. Fallback to Accept-Language header
    if accept_language:
        logging.info(f"No valid cookie. Checking Accept-Language header: {accept_language}")
        # Parse the Accept-Language header manually
        # Format is typically: "en-US,en;q=0.9,de;q=0.8"
        languages = accept_language.split(',')
        for lang_entry in languages:
            # Extract the primary language code (before any quality value or region)
            lang_code = lang_entry.split(';')[0].split('-')[0].strip()
            if lang_code in translator.available_languages:
                logging.info(f"Found valid language in header: '{lang_code}'")
                set_current_language(lang_code)
                return lang_code

    # 3. Default to "en"
    logging.info("No language found in cookie or header. Defaulting to 'en'.")
    set_current_language("en")
    return "en"

def set_current_language(lang_code: str):
    """
    Sets the current language for the application.
    """
    global current_language
    current_language = lang_code

def get_current_language() -> str:
    """
    Returns the current language for the application.
    """
    return current_language