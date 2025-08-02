# app/routers/views.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, Header, Query, Response, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app import config
import json

from app.database import get_session, async_session_maker
from app.services.book_service import BookService
from app.models.models import Chapter
from app.utils.i18n import translator
from app.utils.language import get_language

# Configure templates
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/set-language/{lang_code}")
async def set_language(lang_code: str, response: Response, request: Request):
    """
    Sets the language preference in a cookie and redirects to the referer.
    """
    referer = request.headers.get("referer", "/")
    
    if lang_code in translator.available_languages:
        logging.info(f"Setting language cookie to '{lang_code}' and redirecting to {referer}")
        response = RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="language", value=lang_code, httponly=True, max_age=31536000) # 1 year
        return response
    
    logging.warning(f"Language code '{lang_code}' not available. Redirecting without setting cookie.")
    return RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse)
async def get_root(request: Request, lang: str = Depends(get_language)):
    """
    Renders the main index page.
    """
    _ = translator.get_translator(lang)
    # The new index.html will extend base.html, which provides the sidebar
    return templates.TemplateResponse("index.html", {"request": request, "_": _, "lang": lang})


@router.get("/bookshelf", response_class=HTMLResponse)
async def get_bookshelf(
    request: Request,
    status: Optional[List[str]] = Query(None),
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language)
):
    """
    Renders the bookshelf partial, filtering books by status.
    """
    if status is None:
        status = ["active"]  # Default to 'active' books

    book_service = BookService(session)
    books = await book_service.get_books(statuses=status)
    _ = translator.get_translator(lang)

    return templates.TemplateResponse(
        "_bookshelf.html",
        {
            "request": request,
            "books": books,
            "_": _,
            "lang": lang,
            "available_languages": translator.available_languages,
        },
    )


@router.delete("/book/{book_id}", status_code=200)
async def delete_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Deletes a book and returns an empty response for HTMX.
    """
    book_service = BookService(session)
    await book_service.delete_book(book_id=book_id)
    return HTMLResponse(content="", status_code=200)


@router.get("/book/new/{book_id}", response_class=HTMLResponse)
@router.get("/book/new", response_class=HTMLResponse)
async def get_home(
    request: Request,
    book_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Renders the initial wizard page or resumes a book creation process.
    """
    _ = translator.get_translator(lang)
    book = None
    if book_id:
        book_service = BookService(session)
        try:
            book = await book_service.get_book(book_id)
        except ValueError:
            # Book not found, treat as a new book creation
            book = None

    return templates.TemplateResponse(
        "wizard.html", {"request": request, "book": book, "_": _, "lang": lang}
    )


@router.post("/book", response_class=HTMLResponse)
async def create_book(
    request: Request,
    user_prompt: str = Form(...),
    book_id: Optional[int] = Form(None),
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Creates a new book draft and renders the title step.
    """
    book_service = BookService(session=session)
    if book_id:
        book = await book_service.update_book(book_id=book_id, user_prompt=user_prompt)
    else:
        book = await book_service.create_book_draft(user_prompt=user_prompt)
    ai_comment = await book_service.ai_service.generate_comment(user_story_idea=book.user_prompt)
    _ = translator.get_translator(lang)

    return templates.TemplateResponse(
        "wizard/_title.html",
        {
            "request": request,
            "book": book,
            "ai_comment": ai_comment,
            "_": _,
            "lang": lang,
        },
    )


@router.get("/book/{book_id}/title", response_class=HTMLResponse)
async def get_book_title(
    request: Request,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Renders the title step for an existing book.
    """
    book_service = BookService(session=session)
    book = await book_service.get_book(book_id)
    ai_comment = await book_service.ai_service.generate_comment(user_story_idea=book.user_prompt)
    _ = translator.get_translator(lang)

    return templates.TemplateResponse(
        "wizard/_title.html",
        {
            "request": request,
            "book": book,
            "ai_comment": ai_comment,
            "_": _,
            "lang": lang,
        },
    )


@router.get("/book/{book_id}/world", response_class=HTMLResponse)
async def get_book_world(
    request: Request,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Renders the world step for an existing book.
    """
    book_service = BookService(session)
    book = await book_service.get_book(book_id)
    ai_comment = await book_service.ai_service.generate_comment(user_story_idea=book.user_prompt, user_book_title=book.title)
    _ = translator.get_translator(lang)

    return templates.TemplateResponse(
        "wizard/_world.html",
        {
            "request": request,
            "book": book,
            "ai_comment": ai_comment,
            "_": _,
            "lang": lang,
        },
    )


@router.get("/book/{book_id}/characters", response_class=HTMLResponse)
async def get_book_characters(
    request: Request,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Renders the characters step for an existing book.
    """
    book_service = BookService(session)
    book = await book_service.get_book(book_id)
    ai_comment = await book_service.ai_service.generate_comment(
        user_story_idea=book.user_prompt,
        user_book_title=book.title,
        user_world_description=book.world_description
    )
    _ = translator.get_translator(lang)

    return templates.TemplateResponse(
        "wizard/_characters.html",
        {
            "request": request,
            "book": book,
            "ai_comment": ai_comment,
            "_": _,
            "lang": lang,
            "characters_index": len(book.characters) if book.characters else 0,
        },
    )


@router.put("/book/{book_id}", response_class=HTMLResponse)
async def update_book(
    request: Request,
    book_id: int,
    title: str = Form(None),
    world_description: str = Form(None),
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Updates the book with title or world description and renders the next step.
    """
    book_service = BookService(session)
    _ = translator.get_translator(lang)

    if title:
        book = await book_service.update_book(book_id=book_id, title=title)
        ai_comment = await book_service.ai_service.generate_comment(user_story_idea=book.user_prompt, user_book_title=book.title)
        return templates.TemplateResponse(
            "wizard/_world.html",
            {
                "request": request,
                "book": book,
                "ai_comment": ai_comment,
                "_": _,
                "lang": lang,
            },
        )
    elif world_description:
        book = await book_service.update_book(
            book_id=book_id, world_description=world_description
        )
        ai_comment = await book_service.ai_service.generate_comment(
            user_story_idea=book.user_prompt,
            user_book_title=book.title,
            user_world_description=book.world_description
        )
        return templates.TemplateResponse(
            "wizard/_characters.html",
            {
                "request": request,
                "book": book,
                "ai_comment": ai_comment,
                "_": _,
                "lang": lang,
                "character_index": 0,
            },
        )


@router.get("/book/{book_id}/characters/add", response_class=HTMLResponse)
async def get_character_form(
    request: Request,
    book_id: int | None = None,
    character_index: int = 0,
    lang: str = Depends(get_language),
):
    _ = translator.get_translator(lang)
    return templates.TemplateResponse(
        "wizard/_character_form.html",
        {
            "request": request,
            "book": None,
            "character_index": character_index,
            "_": _,
            "lang": lang,
        },
    )


@router.put("/book/{book_id}/characters")
async def save_characters(
    request: Request,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Parses character data from the form, saves it via the BookService,
    and then finalizes the book.
    """
    book_service = BookService(session=session)
    book = await book_service.get_book(book_id)
    form_data = await request.form()
    
    characters_data = []
    
    # Process dynamic form fields
    character_indices = sorted(
        list(set([
            int(k.split('_')[1])
            for k in form_data.keys()
            if k.startswith('name_') and len(k.split('_')) > 1 and k.split('_')[1].isdigit()
        ]))
    )
    
    protagonist_index = int(form_data.get("is_protagonist", -1))
    
    characters_string = ""
    for i in character_indices:
        name = form_data.get(f"name_{i}")
        description = form_data.get(f"description_{i}")
        characters_string += f"{name}: {description}"
        if name and description:
            characters_data.append({
                "name": name,
                "description": description,
                "is_protagonist": i == protagonist_index
            })

    # Save characters to the database
    await book_service.save_characters_for_book(book_id=book_id, characters_data=characters_data)
    await book_service.update_book(book_id=book_id, chapters_count=config.DEFAULT_NUMBER_OF_CHAPTERS)
    

    ai_comment = await book_service.ai_service.generate_comment(
        user_story_idea=book.user_prompt,
        user_book_title=book.title,
        user_world_description=book.world_description,
        user_characters=characters_string
    )
    _ = translator.get_translator(lang)

    return templates.TemplateResponse(
        "wizard/_chapters.html",
        {
            "request": request,
            "book": book,
            "ai_comment": ai_comment,
            "characters_data": characters_data,
            "_": _,
            "lang": lang
        },
    )
    

@router.put("/book/{book_id}/chapters")
async def save_chapters(
    request: Request,
    book_id: int,
    chapters_count: int = Form(...),
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Parses chapter input from the form, saves it via the BookService,
    and then finalizes the book.
    """
    book_service = BookService(session=session)
    await book_service.update_book(book_id=book_id, chapters_count=chapters_count)
    
    # Fetch the full book details for the processing screen
    book = await book_service.get_book(book_id)
    _ = translator.get_translator(lang)

    return templates.TemplateResponse(
        "wizard/_processing.html",
        {
            "request": request,
            "book": book,
            "characters": book.characters,
            "_": _,
            "lang": lang,
        },
    )


@router.post("/book/{book_id}/generate")
async def generate_book(
    request: Request,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Finalizes and generates the book, then returns a redirect response
    for HTMX or an error partial.
    """
    book_service = BookService(session=session)
    try:
        await book_service.finalize_and_generate_book(book_id=book_id)
        
        # On success, redirect
        return HTMLResponse(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/book/{book_id}"},
        )
    except Exception as e:
        logging.error(f"Error generating book {book_id}: {e}", exc_info=True)
        
        # Mark book as failed
        await book_service.update_book_status(book_id, "failed")
        
        # Re-fetch the book to pass to the template
        book = await book_service.get_book(book_id)

        # Return error partial
        _ = translator.get_translator(lang)
        return templates.TemplateResponse(
            "wizard/_error.html",
            {
                "request": request,
                "book": book,
                "_": _,
                "lang": lang,
                "error_details": str(e)
            },
            status_code=500
        )


@router.get("/book/{book_id}", response_class=HTMLResponse)
async def get_book_dashboard(
    request: Request,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Displays the book dashboard.
    """
    book_service = BookService(session)
    book = await book_service.get_book(book_id)
    _ = translator.get_translator(lang)

    characters = []
    if book.characters:
        for character in book.characters:
            char_type = _("protagonist") if character.is_protagonist else _("supporting")
            characters.append(
                f"{character.name}, {_('role')}: {char_type}, {_('summary')}: {character.description}"
            )
    
    # Calculate the next chapter to write (lowest chapter number with status 'draft')
    next_chapter_to_write_number = None
    if book.chapters:
        draft_chapters = [ch for ch in book.chapters if ch.status == 'draft']
        if draft_chapters:
            next_chapter_to_write_number = min(ch.chapter_number for ch in draft_chapters)

    # For now, just a simple confirmation. A full template is out of scope.
    return templates.TemplateResponse(
        "book_dashboard.html",
        {
            "request": request,
            "book": book,
            "_": _,
            "lang": lang,
            "characters": book.characters,
            "subtitle": book.llm_concept.get("title"),
            "synopsis": book.llm_concept.get("premise"),
            "next_chapter_to_write_number": next_chapter_to_write_number,
        },
    )


# Placeholder routes for Phase 2 - Chapter Generation and Streaming
@router.get("/book/{book_id}/chapter/{chapter_id}", response_class=HTMLResponse)
async def get_chapter_view(
    request: Request,
    book_id: int,
    chapter_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Displays a specific chapter.
    """
    _ = translator.get_translator(lang)
    book_service = BookService(session)
    
    # Get the book with all its chapters
    book = await book_service.get_book(book_id)
    
    # Find the specific chapter
    chapter = None
    for ch in book.chapters:
        if ch.id == chapter_id:
            chapter = ch
            break
    
    if not chapter:
        return HTMLResponse(content=f"Chapter with ID {chapter_id} not found.", status_code=404)
    
    # Determine previous and next chapter IDs
    previous_chapter_id = None
    next_chapter_id = None
    
    # Sort chapters by chapter_number
    sorted_chapters = sorted(book.chapters, key=lambda ch: ch.chapter_number)
    
    # Find the current chapter's index in the sorted list
    current_index = None
    for i, ch in enumerate(sorted_chapters):
        if ch.id == chapter_id:
            current_index = i
            break
    
    # Determine previous and next chapter IDs
    if current_index is not None:
        if current_index > 0:
            previous_chapter_id = sorted_chapters[current_index - 1].id
        if current_index < len(sorted_chapters) - 1:
            next_chapter_id = sorted_chapters[current_index + 1].id
    
    return templates.TemplateResponse(
        "chapter_view.html",
        {
            "request": request,
            "book": book,
            "chapter": chapter,
            "previous_chapter_id": previous_chapter_id,
            "next_chapter_id": next_chapter_id,
            "_": _,
            "lang": lang,
        },
    )


@router.get("/book/{book_id}/chapter/{chapter_id}/write", response_class=HTMLResponse)
async def get_chapter_writing_ui(
    request: Request,
    book_id: int,
    chapter_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Displays the chapter writing UI.
    """
    book_service = BookService(session)
    _ = translator.get_translator(lang)
    
    try:
        # Get the book and chapter
        book = await book_service.get_book(book_id)
        chapter = None
        
        # Find the specific chapter
        for ch in book.chapters:
            if ch.id == chapter_id:
                chapter = ch
                break
        
        if not chapter:
            raise ValueError(f"Chapter with ID {chapter_id} not found.")
        
        # Return the writing room template
        return templates.TemplateResponse(
            "writing_room.html",
            {
                "request": request,
                "book": book,
                "chapter": chapter,
                "_": _,
                "lang": lang,
            },
        )
    except Exception as e:
        logging.error(f"Error getting chapter writing UI: {e}", exc_info=True)
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


async def finalize_chapter_writing(chapter_id: int, full_content: str, part: int):
    """Saves the final chapter content and updates status in the background."""
    session = None
    try:
        # It's crucial this task gets its own session
        session = async_session_maker()
        chapter = await session.get(Chapter, chapter_id)
        if chapter:
            if part == 1:
                chapter.content = full_content
                chapter.status = "part1_completed"
            else: # part == 2
                part1_content = chapter.content or ""
                chapter.content = part1_content + "\n\n" + full_content
                chapter.status = "completed"
            
            session.add(chapter)
            await session.commit()
            logging.info(f"Successfully finalized chapter {chapter_id}, part {part}.")
    except Exception as e:
        logging.error(f"Background finalization failed for chapter {chapter_id}: {e}", exc_info=True)
    finally:
        if session:
            await session.close()


@router.post("/book/{book_id}/chapter/{chapter_id}/generate")
async def generate_chapter(
    request: Request,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    part: int = Form(...),
    user_directives: str = Form(""),
    session: AsyncSession = Depends(get_session),
):
    """
    Sets up the chapter and returns a streaming response.
    """
    logging.info(f"Starting chapter generation for chapter_id={chapter_id}, part={part}")
    
    try:
        book_service = BookService(session)
        
        # Setup phase
        chapter = await session.get(Chapter, chapter_id)
        if not chapter:
            return HTMLResponse("Chapter not found", status_code=404)

        chapter.status = f"writing_part{part}"
        chapter.user_directives = user_directives
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        prompt = await book_service.build_chapter_prompt(chapter, part, user_directives)
        
        # Return a simple response that triggers the SSE connection
        return HTMLResponse(f"""
        <div id="streaming-container" 
             hx-ext="sse"
             sse-connect="/book/{chapter_id}/generate-stream?part={part}&user_directives={user_directives}"
             sse-swap="message">
            <div class="streaming-content"></div>
        </div>
        """)
        
    except Exception as e:
        logging.error(f"Error in generate_chapter for chapter {chapter_id}: {e}", exc_info=True)
        raise

# Add this new GET endpoint for SSE
@router.get("/book/{book_id}/chapter/{chapter_id}/generate-stream")
async def generate_chapter_stream(
    request: Request,
    book_id: int,
    chapter_id: int,
    part: int = Query(...),
    user_directives: str = Query(""),
    session: AsyncSession = Depends(get_session),
):
    """
    SSE endpoint for streaming chapter generation.
    """
    logging.info(f"Starting SSE streaming for chapter_id={chapter_id}, part={part}")
    
    try:
        book_service = BookService(session)
        
        # Get the chapter
        chapter = await session.get(Chapter, chapter_id)
        if not chapter:
            logging.error(f"Chapter {chapter_id} not found")
            return HTMLResponse("Chapter not found", status_code=404)

        # Update chapter status
        chapter.status = f"writing_part{part}"
        chapter.user_directives = user_directives
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        # Build the prompt
        prompt = await book_service.build_chapter_prompt(chapter, part, user_directives)
        logging.info(f"Successfully built prompt for chapter {chapter_id}")

        # Create background tasks for finalization
        background_tasks = BackgroundTasks()

        async def stream_wrapper():
            streaming_session = None
            try:
                streaming_session = async_session_maker()
                logging.info(f"Created new session for streaming chapter {chapter_id}")
                
                full_content = ""
                try:
                    logging.info(f"Starting AI streaming for chapter {chapter_id}")
                    streaming_book_service = BookService(streaming_session)
                    
                    async for chunk in streaming_book_service.ai_service.generate_response_stream(prompt):
                        content = chunk.get("data", "")
                        full_content += content
                        logging.info(f"Streaming chunk for chapter {chapter_id}: {content}")
                        
                        yield ServerSentEvent(
                            data=content,
                            event="message",
                            id=str(chapter_id)
                        )
                    
                    logging.info(f"AI streaming completed for chapter {chapter_id}, content length: {len(full_content)}")
                    
                    # Schedule background finalization
                    background_tasks.add_task(finalize_chapter_writing, chapter_id, full_content, part)

                    yield ServerSentEvent(
                        data="Stream finished.",
                        event="complete",
                        id=str(chapter_id)
                    )
                except Exception as e:
                    logging.error(f"Streaming failed for chapter {chapter_id}: {e}", exc_info=True)
                    yield ServerSentEvent(
                        data="An error occurred during streaming.",
                        event="error",
                        id=str(chapter_id)
                    )
            finally:
                if streaming_session:
                    await streaming_session.close()
                    logging.info(f"Closed streaming session for chapter {chapter_id}")

        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }

        return EventSourceResponse(stream_wrapper(), headers=headers)
        
    except Exception as e:
        logging.error(f"Error in generate_chapter_stream for chapter {chapter_id}: {e}", exc_info=True)
        raise
