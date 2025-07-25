# app/routers/views.py
from fastapi import APIRouter, Request, Depends, Form, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app.services.book_service import BookService
from app.utils.i18n import translator

# Configure templates
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


def get_language(accept_language: str = Header(None)) -> str:
    if accept_language:
        # Parse the Accept-Language header manually
        # Format is typically: "en-US,en;q=0.9,de;q=0.8"
        languages = accept_language.split(',')
        for lang_entry in languages:
            # Extract the primary language code (before any quality value or region)
            lang_code = lang_entry.split(';')[0].split('-')[0].strip()
            if lang_code in translator.available_languages:
                return lang_code
    return "en"  # Default language


@router.get("/", response_class=HTMLResponse)
async def get_home(request: Request, lang: str = Depends(get_language)):
    # This will render our main page.
    _ = translator.get_translator(lang)
    return templates.TemplateResponse(
        "index.html", {"request": request, "_": _, "lang": lang}
    )


@router.post("/book", response_class=HTMLResponse)
async def create_book(
    request: Request,
    user_prompt: str = Form(...),
    session: Session = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Creates a new book draft and renders the title step.
    """
    book_service = BookService(session=session)
    book = book_service.create_book_draft(user_prompt=user_prompt)
    ai_comment = book_service.ai_service.generate_comment(user_story_idea=book.user_prompt)
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


@router.put("/book/{book_id}", response_class=HTMLResponse)
async def update_book(
    request: Request,
    book_id: int,
    title: str = Form(None),
    world_description: str = Form(None),
    session: Session = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Updates the book with title or world description and renders the next step.
    """
    book_service = BookService(session)
    _ = translator.get_translator(lang)

    if title:
        book = book_service.update_book(book_id=book_id, title=title)
        ai_comment = book_service.ai_service.generate_comment(user_story_idea=book.user_prompt, user_book_title=book.title)
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
        book = book_service.update_book(
            book_id=book_id, world_description=world_description
        )
        ai_comment = book_service.ai_service.generate_comment(
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
            "book_id": book_id,
            "character_index": character_index,
            "_": _,
            "lang": lang,
        },
    )


@router.put("/book/{book_id}/characters")
async def save_characters(
    request: Request,
    book_id: int,
    session: Session = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Parses character data from the form, saves it via the BookService,
    and then finalizes the book.
    """
    book_service = BookService(session=session)
    book = book_service.get_book(book_id)
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

    ai_comment = book_service.ai_service.generate_comment(
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
            "_": _,
            "lang": lang
        },
    )
    

@router.put("/book/{book_id}/chapters")
async def save_chapters(
    request: Request,
    book_id: int,
    chapters_count: int = Form(...),
    session: Session = Depends(get_session),
    lang: str = Depends(get_language),
):
    """
    Parses chapter input from the form, saves it via the BookService,
    and then finalizes the book.
    """
    book_service = BookService(session=session)
    form_data = await request.form()

    book_service.update_book(book_id=book_id, chapters_count=chapters_count)
    book_service.finalize_and_generate_book(book_id=book_id)

    return RedirectResponse(
        url=f"/book/{book_id}/read",
        status_code=303
    )
