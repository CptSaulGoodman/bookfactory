# Refactoring Plan for app/routers/views.py

This plan outlines the steps to refactor the `app/routers/views.py` file to improve modularity and maintainability.

### 1. Create New Utility File

- **Action:** Create a new file `app/utils/text_parser.py`.
- **Details:** Move the `parse_markdown` function from `app/routers/views.py` into this new file.

### 2. Create New Router Files

- **Action:** Create two new router files.
- **Files:**
  - `app/routers/wizard.py`: For the book creation wizard.
  - `app/routers/book.py`: For managing existing books and chapters.

### 3. Move Wizard Routes

- **Action:** Move all wizard-related endpoints from `app/routers/views.py` to `app/routers/wizard.py`.
- **Functions to Move:**
  - `get_home`
  - `create_book`
  - `get_book_title`
  - `get_book_world`
  - `get_book_characters`
  - `update_book`
  - `get_character_form`
  - `save_characters`
  - `save_chapters`
  - `generate_book`

### 4. Move Book and Chapter Routes

- **Action:** Move all book and chapter management endpoints from `app/routers/views.py` to `app/routers/book.py`.
- **Functions to Move:**
  - `get_book_dashboard`
  - `get_chapter_view`
  - `get_chapter_writing_ui`
  - `finalize_chapter_writing`
  - `generate_chapter`
  - `generate_chapter_stream`

### 5. Clean Up `app/routers/views.py`

- **Action:** Remove all the moved functions from `app/routers/views.py`.
- **Remaining Functions:**
  - `set_language`
  - `get_root`
  - `get_bookshelf`
  - `delete_book`

### 6. Update `app/main.py`

- **Action:** Import and include the new routers in the main FastAPI application.
- **Details:**
  - Add `from app.routers import wizard, book`.
  - Add `app.include_router(wizard.router)`.
  - Add `app.include_router(book.router)`.