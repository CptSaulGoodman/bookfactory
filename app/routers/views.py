# app/routers/views.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, Header, Query, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app import config
import json

from app.database import get_session
from app.services.book_service import BookService
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
    book_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Finalizes and generates the book, then returns a redirect response
    for HTMX.
    """
    book_service = BookService(session=session)
    await book_service.finalize_and_generate_book(book_id=book_id)

    # HTMX needs a 200 OK with a HX-Redirect header for client-side redirect
    return HTMLResponse(
        content="",
        status_code=200,
        headers={"HX-Redirect": f"/book/{book_id}"},
    )


@router.get("/book/{book_id}", response_class=HTMLResponse)
async def get_book_final(
    request: Request,
    book_id: int,
    session: AsyncSession = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Displays the final, generated book.
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

    chapters = book.llm_concept.get("chapters")

    # For now, just a simple confirmation. A full template is out of scope.
    return templates.TemplateResponse(
        "wizard/_final_book.html",
        {
            "request": request,
            "book": book,
            "_": _,
            "lang": lang,
            "characters": book.characters,
            "subtitle": book.llm_concept.get("title"),
            "synopsis": book.llm_concept.get("premise"),
            "chapters": chapters,
        },
    )
