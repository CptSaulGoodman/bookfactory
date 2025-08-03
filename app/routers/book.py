# app/routers/book.py
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
from app.utils.text_parser import parse_markdown

# Configure templates
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


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

    formatted_content = parse_markdown(chapter.content) if chapter.content else ""
    
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
            "formatted_content": formatted_content,
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
        
        # Parse markdown for existing content
        formatted_content = parse_markdown(chapter.content) if chapter.content else ""
        
        # Return the writing room template
        return templates.TemplateResponse(
            "writing_room.html",
            {
                "request": request,
                "book": book,
                "chapter": chapter,
                "formatted_content": formatted_content,
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
             sse-connect="/book/{chapter.book_id}/chapter/{chapter_id}/generate-stream?part={part}&user_directives={user_directives}"
             sse-swap="message">
            <div class="streaming-content"></div>
        </div>
        """)
        
    except Exception as e:
        logging.error(f"Error in generate_chapter for chapter {chapter_id}: {e}", exc_info=True)
        raise

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
                        logging.debug(f"Streaming chunk for chapter {chapter_id}: {content}")
                        
                        yield ServerSentEvent(
                            data=content,
                            event="message",
                            id=str(chapter_id)
                        )
                    
                    logging.info(f"AI streaming completed for chapter {chapter_id}, content length: {len(full_content)}")
                    
                    # Call finalization directly since we can't use BackgroundTasks in GET
                    # We'll do this in a separate task to avoid blocking the response
                    import asyncio
                    asyncio.create_task(finalize_chapter_writing(chapter_id, full_content, part))

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