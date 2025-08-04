# Book Factory 📖✨

An AI-powered, interactive book generation application designed to provide a magical storytelling experience. Built with a modern Python backend and a lightweight, responsive frontend, it allows users to create, shape, and read unique books on the fly.

> Full disclosure: This project is largely "vibe-coded" to try out how far I can push the current state of AI (spoiler: It needed quite a bit of manual tweaking). Expect some rough edges and not best practice in code quality - treat it as POC and as having fun with what's possible nowadays.

## Version 2.0 Highlights (What's New)

This version represents a complete architectural overhaul from the original command-line proof-of-concept. The application has been rebuilt from the ground up to be a fully-featured, interactive web application.

*   **Full Web Interface:** The application is now served via **FastAPI** with a **Jinja2** and **HTMX**-powered frontend, replacing the original command-line interface.
*   **Interactive Book Wizard:** A new, mobile-first wizard guides the user through the book creation process, from initial idea to defining the world and characters.
*   **Persistent Database:** Book data is now stored in a **SQLite** database using **SQLModel** as the ORM, replacing the static, in-memory sample data.
*   **Real-time Chapter Generation:** Chapters are written live to the screen using **Server-Sent Events (SSE)**, creating a "magic quill" effect for the user.
*   **Dynamic Bookshelf:** A persistent, filterable bookshelf serves as the main dashboard for browsing, reading, and managing all created books.
*   **Internationalization (i18n):** The UI now supports multiple languages, which can be selected by the user.
*   **AI Companion:** The AI provides fun, encouraging comments throughout the creation process to make it more engaging.
*   **Contextual Story Continuation:** The app now generates a summary of the story after each chapter is written. This summary is then used as context for generating the *next* chapter, ensuring narrative consistency.

## Features

-   **Interactive Creation Wizard**: A step-by-step guide to bring a story idea to life.
-   **AI-Powered Content Generation**: Creates book concepts, detailed character profiles, and chapter synopses using a structured LLM output.
-   **Live Chapter Writing**: Watch the AI write chapters in real-time with the ability to provide custom directives and guidance.
-   **Persistent Bookshelf**: All your created books are saved and can be read or continued at any time.
-   **Dynamic & Responsive UI**: Built with HTMX for a fast, single-page application feel without the overhead of a large JavaScript framework.
-   **Database Persistence**: Uses SQLite and SQLModel for robust, async-first data storage.
-   **Easy Configuration**: Point the app to any OpenAI-compatible API endpoint (e.g., Ollama).

## Architecture

The application is built on a modern, asynchronous Python stack:

-   **Backend**: **FastAPI** for high-performance, async web serving.
-   **Database**: **SQLite** with **SQLModel** for a Pythonic, async-first ORM.
-   **Frontend**: **Jinja2** for server-side HTML templating, supercharged with **HTMX** for frontend interactivity.
-   **AI Integration**: **LangChain** orchestrates communication with the LLM, handling structured output and streaming.
-   **Context Management**: For narrative continuity, the application currently generates a **summary of previous chapters** to feed into the prompt for the next chapter. A more advanced RAG implementation is planned for a future release.

## Prerequisites

-   Python 3.9+
-   An OpenAI-compatible API endpoint (e.g., Ollama, Llama.cpp, or a cloud provider).
-   Access to a compatible LLM and embedding model through the endpoint.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd bookfactory
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    The application requires several packages for the web server, database, and AI services. For production use, it's also recommended to install `alembic` for database migrations.
    ```bash
    pip install "fastapi[all]" uvicorn sqlmodel aiosqlite langchain-openai langchain-core langchain-chroma alembic
    ```

## Configuration

All configuration is located in `app/config/settings.py`. To override default settings without committing sensitive data, create a local configuration file:

1.  **Copy the example file:**
    ```bash
    cp app/config/settings_local.py.example app/config/settings_local.py
    ```

2.  **Edit `app/config/settings_local.py`** and add your settings. For example, to use a local Ollama instance:
    ```python
    # Example for Ollama in app/config/settings_local.py
    OPENAI_API_BASE = "http://localhost:11434/v1"
    OPENAI_API_KEY = "ollama"
    LLM_MODEL = "gemma2:9b"
    EMBEDDING_MODEL = "nomic-embed-text"
    ```

3.  **Ensure your models are available** if using Ollama:
    ```bash
    ollama pull gemma2:9b
    ollama pull nomic-embed-text
    ```

## Running the Application

### Development Server

For development, run the application using `uvicorn`, which provides auto-reloading.

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

### Production Deployment (Systemd Service)

For running the app as a persistent service on a Linux server, creating a `systemd` service file is recommended.

1.  **Create the service file:**
    ```bash
    sudo nano /etc/systemd/system/bookfactory.service
    ```

2.  **Paste the following configuration**, making sure to replace `/path/to/your/project` and `your_user` with your actual project path and username.

    ```ini
    [Unit]
    Description=Book Factory Application
    After=network.target

    [Service]
    User=your_user
    Group=your_user
    WorkingDirectory=/path/to/your/project
    Environment="PATH=/path/to/your/project/.venv/bin"
    ExecStart=/path/to/your/project/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
    ```

3.  **Enable and start the service:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable bookfactory.service
    sudo systemctl start bookfactory.service
    ```

4.  **Check the status:**
    ```bash
    sudo systemctl status bookfactory.service
    ```

## Database Migrations

The application uses **SQLModel**, which works with **Alembic** for database migrations. This is essential for managing changes to your database schema after the initial setup.

1.  **Initialize Alembic** (only needs to be done once):
    ```bash
    alembic init alembic
    ```

2.  **Configure Alembic:**
    *   **Edit `alembic.ini`:** Find the `sqlalchemy.url` line and set it to your database URL from `app/config/settings.py`.
        ```ini
        sqlalchemy.url = sqlite:///book_db/bookfactory.db
        ```
    *   **Edit `alembic/env.py`:** Import your SQLModel base model and set it as the `target_metadata`.
        ```python
        # Near the top of the file
        from app.models.models import SQLModel  # Adjust the import path if needed

        # ...

        # Find the line 'target_metadata = None' and replace it with:
        target_metadata = SQLModel.metadata
        ```

3.  **Creating a New Migration:**
    Whenever you change your models in `app/models/models.py` (e.g., add a new column), generate a new migration script:
    ```bash
    alembic revision --autogenerate -m "A description of your changes"
    ```

4.  **Applying a Migration:**
    Apply the changes to your database with the `upgrade` command:
    ```bash
    alembic upgrade head
    ```