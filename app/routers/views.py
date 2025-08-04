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




