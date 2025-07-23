# Book Factory

An AI-powered book generation application that creates stories using LangChain and any OpenAI-compatible API endpoint (including Ollama). The application generates book concepts, character sheets, events, and complete chapters based on configurable parameters.

## 🏗️ Architecture

The application follows a modular architecture with clear separation of concerns:

```
app/
├── config/          # Configuration settings
├── models/          # Data structures for books and characters
├── data/            # Sample data and data management
├── services/        # Core business logic and AI integration
├── prompts/         # AI prompt templates (markdown files)
│   ├── *.md         # Individual prompt templates
│   └── templates.py # Dynamic template loader
└── utils/           # Helper functions and utilities
```

## 🚀 Features

- **Book Concept Generation**: Create initial book outlines with chapter summaries
- **Character Development**: Generate detailed character sheets and profiles
- **Event Creation**: Generate story events for individual chapters
- **Chapter Writing**: AI-powered chapter generation in multiple parts
- **Vector Database**: Character embedding and retrieval using Chroma
- **Dynamic Template System**: Markdown-based prompt templates with dynamic loading
- **Modular Design**: Clean, maintainable, and extensible architecture

## 📋 Prerequisites

- Python 3.8+
- An OpenAI-compatible API endpoint (e.g., Ollama, Llama.cpp, or a cloud provider)
- Access to a compatible LLM and embedding model through the endpoint

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bookfactory
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install langchain-openai langchain-core langchain-chroma httpx
   ```

4. **Configure your AI Provider**

   All configuration is located in `app/config/`. The default settings are in `settings.py`.

   To add your local configuration (like API keys) without committing them, create a local settings file:
   ```bash
   cp app/config/settings_local.py.example app/config/settings_local.py
   ```
   Now edit `app/config/settings_local.py` and add your settings. For example:
   ```python
   # Example for Ollama in app/config/settings_local.py
   OPENAI_API_BASE = "http://localhost:11434/v1"
   OPENAI_API_KEY = "ollama"
   LLM_MODEL = "phi4:latest"
   EMBEDDING_MODEL = "nomic-embed-text:v1.5"
   ```

   If you are using Ollama, ensure the models are pulled:
   ```bash
   ollama pull phi4:latest
   ollama pull nomic-embed-text:v1.5
   ```

## 🎯 Usage

### Basic Usage

Run the main application:
```bash
python -m app.main
```

### Available Functions

The application provides several generation functions that can be enabled in `main.py`:

- **Initial Concept**: Generate book outline and chapter summaries
- **Character Sheets**: Create detailed character profiles
- **Events**: Generate story events for chapters
- **Chapters**: Write complete chapters with AI

### Configuration

All settings are configured in `app/config/settings.py`. For local customizations, especially for sensitive data like API keys, it is highly recommended to create a `app/config/settings_local.py` file. Any values set in `settings_local.py` will override the defaults in `settings.py`.

Commonly configured settings include:

- `OPENAI_API_BASE`: The base URL for the API endpoint.
- `OPENAI_API_KEY`: The API key for your provider.
- `LLM_MODEL`: The name of the chat model to use.
- `EMBEDDING_MODEL`: The name of the embedding model to use.

## 📁 Project Structure

| Module | Purpose |
|--------|---------|
| `config/` | Application settings and configuration |
| `models/` | Data structures for books and characters |
| `data/` | Sample data and data management |
| `services/` | Core business logic and AI integration |
| `prompts/` | AI prompt templates (markdown files + dynamic loader) |
| `utils/` | Helper functions and utilities |

### Template System Architecture

The prompt system uses a dynamic template loader with the following components:

- **Markdown Files** (`*.md`): Individual prompt templates stored as markdown files
- **TemplateLoader Class**: Handles file loading, caching, and template discovery
- **Dynamic Functions**: 
  - `get_template()`: Load and format templates by name
  - `list_available_templates()`: Discover available templates
  - `template_exists()`: Check if a template exists

This architecture provides:
- **Easy editing**: Templates can be modified without code changes
- **Version control**: Template changes are tracked in git
- **Dynamic loading**: New templates can be added without restarting the application
- **Error handling**: Proper logging and error reporting for missing templates

## 🔧 Customization

### Adding New Prompts
The application uses a dynamic template system with markdown files:

1. **Create a new template file**: Add a new `.md` file in `app/prompts/` directory
2. **Use the template**: Call `get_template("your_template_name", **params)` in your code
3. **Template discovery**: Use `list_available_templates()` to see all available templates

Example:
```python
from app.prompts.templates import get_template

prompt = get_template("my_custom_template", 
                     param1="value1", 
                     param2="value2")
```

### Modifying Data Models
Update data structures in `app/models/` directory

### Changing AI Models
Modify model settings in `app/config/settings.py`

## 🤝 Contributing

1. Follow the existing modular architecture
2. Add type hints to all functions
3. Include docstrings for new modules
4. Test your changes before submitting
