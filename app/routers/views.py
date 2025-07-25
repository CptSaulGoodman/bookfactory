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
        {"request": request, "book_id": book.id}
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
    Delegates to the BookService to update a book draft and returns
    the next part of the wizard.
    """
    book_service = BookService(session=session)
    book = book_service.update_book_draft(
        book_id=book_id,
        title=title,
        world_description=world_description
    )
    
    next_template = ""
    context = {"request": request, "book_id": book.id}

    if title:
        next_template = "wizard/_world.html"
    elif world_description:
        next_template = "wizard/_characters.html" 
    
    return templates.TemplateResponse(next_template, context)

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