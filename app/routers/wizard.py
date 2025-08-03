# app/routers/wizard.py
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