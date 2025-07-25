# app/routers/views.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app.services.book_service import BookService

# Configure templates
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    # This will render our main page.
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/book", response_class=HTMLResponse)
async def create_book(
    request: Request,
    user_prompt: str = Form(...),
    session: Session = Depends(get_session),
):
    """
    Creates a new book draft and renders the title step.
    """
    book_service = BookService(session=session)
    book = book_service.create_book_draft(user_prompt=user_prompt)
    ai_comment = book_service.ai_service.generate_comment(user_input=book.user_prompt)
    
    return templates.TemplateResponse(
        "wizard/_title.html",
        {"request": request, "book": book, "ai_comment": ai_comment},
    )


@router.put("/book/{book_id}", response_class=HTMLResponse)
async def update_book(
    request: Request,
    book_id: int,
    title: str = Form(None),
    world_description: str = Form(None),
    session: Session = Depends(get_session),
):
    """
    Updates the book with title or world description and renders the next step.
    """
    book_service = BookService(session)

    if title:
        book = book_service.update_book(book_id=book_id, title=title)
        ai_comment = book_service.ai_service.generate_comment(user_input=book.title)
        return templates.TemplateResponse(
            "wizard/_world.html",
            {"request": request, "book": book, "ai_comment": ai_comment},
        )
    elif world_description:
        book = book_service.update_book(
            book_id=book_id, world_description=world_description
        )
        ai_comment = book_service.ai_service.generate_comment(
            user_input=book.world_description
        )
        return templates.TemplateResponse(
            "wizard/_characters.html",
            {"request": request, "book": book, "ai_comment": ai_comment},
        )


@router.get("/book/{book_id}/characters/add", response_class=HTMLResponse)
async def get_character_form(request: Request, book_id: int | None = None, character_index: int = 0):
    return templates.TemplateResponse(
        "wizard/_character_form.html",
        {"request": request, "book_id": book_id, "character_index": character_index},
    )


@router.put("/book/{book_id}/characters")
async def save_characters(
    request: Request,
    book_id: int,
    session: Session = Depends(get_session),
):
    """
    Parses character data from the form, saves it via the BookService,
    and then finalizes the book.
    """
    book_service = BookService(session=session)
    form_data = await request.form()
    
    characters_data = []
    
    # Process dynamic form fields
    character_indices = sorted(
        list(set([int(k.split('_')[1]) for k in form_data.keys() if k.startswith('name_')]))
    )
    
    protagonist_index = int(form_data.get("is_protagonist", -1))
    
    for i in character_indices:
        name = form_data.get(f"name_{i}")
        description = form_data.get(f"description_{i}")
        if name and description:
            characters_data.append({
                "name": name,
                "description": description,
                "is_protagonist": i == protagonist_index
            })

    book_service.save_characters_for_book(book_id, characters_data)
    book_service.finalize_and_generate_book(book_id=book_id)

    return RedirectResponse(
        url=f"/book/{book_id}/read",
        status_code=303
    )
