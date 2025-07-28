"""Configuration settings for the book generation application."""

# Language Configuration (the language the book will be written in)
LANGUAGE = "german"

# AI Provider Configuration
# Point this to any OpenAI-compatible API endpoint
OPENAI_API_BASE = "http://192.168.22.251:8090/v1"
OPENAI_API_KEY = "ollama"  # For Ollama, the API key can be any string

# AI Model Configuration
LLM_MODEL = "gemma-3-4b"
EMBEDDING_MODEL = "embedder"

# Database Configuration
DATABASE_URL = "sqlite:///book_db/bookfactory.db"

# Vector Database Configuration
DB_LOCATION = "book_db"
COLLECTION_NAME = "characters"
RETRIEVER_K = 5

# Book Generation Settings
DEFAULT_WORLD_PARAMS = "a mess hall during world war 2"
DEFAULT_STORY_BITS = "a cook serving food to his fellow soldiers"
DEFAULT_NUMBER_OF_CHAPTERS = 5
DEFAULT_NUMBER_OF_CHARS = 5
DEFAULT_NUMBER_OF_MAIN_CHARS = 2
DEFAULT_NUMBER_OF_SUPPORT_CHARS = 3
DEFAULT_NUMBER_OF_EVENTS = 3 
