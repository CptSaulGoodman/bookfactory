# app/services/book_service.py
import json
from typing import List, Optional
from sqlmodel import Session, select
from app.models.models import Book, Character
from app.services.ai_service import AIService
from app.services.book_generator import BookGenerator

class BookService:
    def __init__(self, session: Session):
        self.session = session
        # Instantiate AIService and BookGenerator
        self.ai_service = AIService()
        self.book_generator = BookGenerator(ai_service=self.ai_service)

    def get_book(self, book_id: int) -> "Book":
        """
        Retrievis a book by its ID.
        """
        book = self.session.get(Book, book_id)
        if not book:
            # In a real app, a more specific exception would be better.
            raise ValueError(f"Book with ID {book_id} not found.")
        return book

    def get_books(self, statuses: Optional[List[str]] = None) -> List[Book]:
        """
        Retrieves books, optionally filtered by status, ordered by creation date.
        """
        query = select(Book).order_by(Book.created_at.desc())
        if statuses:
            query = query.where(Book.status.in_(statuses))
        
        books = self.session.exec(query).all()
        return books

    def delete_book(self, book_id: int) -> None:
        """
        Deletes a book by its ID.
        """
        book = self.session.get(Book, book_id)
        if book:
            self.session.delete(book)
            self.session.commit()

    def create_book_draft(self, user_prompt: str) -> Book:
        """
        Creates a new Book instance with a 'draft' status.
        """
        book = Book(user_prompt=user_prompt, status="draft")
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def update_book(self, book_id: int, **kwargs) -> Book:
        """
        Updates a book with the given attributes.
        """
        book = self.get_book(book_id)
        for key, value in kwargs.items():
            if hasattr(book, key) and value is not None:
                setattr(book, key, value)
        
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def save_characters_for_book(self, book_id: int, characters_data: list[dict]) -> None:
        """
        Saves character data for a specific book.
        """
        book = self.session.get(Book, book_id)
        
        # Simple validation: Ensure only one protagonist
        protagonist_count = sum(1 for char in characters_data if char.get('is_protagonist'))
        if protagonist_count != 1:
            raise ValueError("There must be exactly one protagonist.")

        for char_data in characters_data:
            character = Character(
                name=char_data['name'],
                description=char_data['description'],
                is_protagonist=char_data.get('is_protagonist', False),
                book_id=book.id
            )
            self.session.add(character)
        
        self.session.commit()

    def finalize_and_generate_book(self, book_id: int) -> Book:
        """
        Marks the book as 'active' and triggers the generation process.
        """
        book = self.session.get(Book, book_id)
        
        # Call the generator
        llm_concept = self.book_generator.generate_initial_concept_for_book(book)
        
        # Convert the Pydantic model to a dictionary for database storage
        book.llm_concept = llm_concept.dict()

        book.status = "active"
        
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)

        return book