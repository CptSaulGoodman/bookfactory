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
    session: Session = Depends(get_session)
):
    """
    Delegates to the BookService to create a new book draft and returns
    the next step of the wizard.
    """
    book_service = BookService(session=session)
    book = book_service.create_book_draft(user_prompt=user_prompt)

    return templates.TemplateResponse(
        "wizard/_title.html",
        {"request": request, "book": book}
    )

@router.put("/book/{book_id}", response_class=HTMLResponse)
async def update_book(
    request: Request,
    book_id: int,
    title: str = Form(None),
    world_description: str = Form(None),
    session: Session = Depends(get_session)
):
    """
    Updates a book draft, generates all necessary AI comments for the
    timeline view, and returns the next part of the wizard.
    """
    book_service = BookService(session=session)
    book = book_service.update_book_draft(
        book_id=book_id,
        title=title,
        world_description=world_description
    )
    
    next_template = ""
    context = {"request": request, "book": book}

    if title:
        # Generate the AI comment for the title
        context["title_ai_comment"] = book_service.ai_service.generate_comment(user_input=book.title)
        next_template = "wizard/_world.html"
    elif world_description:
        # Generate AI comments for both title and world
        context["title_ai_comment"] = book_service.ai_service.generate_comment(user_input=book.title)
        context["world_ai_comment"] = book_service.ai_service.generate_comment(user_input=book.world_description)
        next_template = "wizard/_characters.html"
    
    return templates.TemplateResponse(next_template, context)


@router.get("/book/{book_id}/characters/add", response_class=HTMLResponse)
async def get_character_form(request: Request, book_id: int, character_index: int = 0):
    return templates.TemplateResponse(
        "wizard/_character_form.html",
        {"request": request, "book_id": book_id, "character_index": character_index}
    )


@router.put("/book/{book_id}/characters")
async def save_characters(
    request: Request,
    book_id: int,
    session: Session = Depends(get_session)
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

@router.post("/book/{book_id}/generate")
async def generate_book(
    book_id: int,
    session: Session = Depends(get_session)
):
    """
    Delegates to the BookService to finalize the book and trigger
    the generation process.
    """
    book_service = BookService(session=session)
    book_service.finalize_and_generate_book(book_id=book_id)

    # Redirect to a placeholder page for the created book
    return RedirectResponse(url=f"/book/{book_id}/read", status_code=303)