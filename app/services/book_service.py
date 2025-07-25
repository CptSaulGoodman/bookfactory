# app/services/book_service.py
import json # Add this import
from sqlmodel import Session
from app.models.models import Book
from app.services.ai_service import AIService # Add this import
from app.services.book_generator import BookGenerator

class BookService:
    def __init__(self, session: Session):
        self.session = session
        # Instantiate AIService and BookGenerator
        self.ai_service = AIService()
        self.book_generator = BookGenerator(ai_service=self.ai_service)

    def create_book_draft(self, user_prompt: str) -> Book:
        """
        Creates a new Book instance with a 'draft' status.
        """
        book = Book(user_prompt=user_prompt, status="draft")
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book

    def update_book_draft(
        self, 
        book_id: int, 
        title: str | None = None, 
        world_description: str | None = None
    ) -> Book:
        """
        Updates the book draft with the provided details.
        """
        book = self.session.get(Book, book_id)
        if title:
            book.title = title
        if world_description:
            book.world_description = world_description
        
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book
        
    def finalize_and_generate_book(self, book_id: int) -> Book:
        """
        Marks the book as 'active' and triggers the generation process.
        """
        book = self.session.get(Book, book_id)
        
        # Call the generator
        concept_json_string = self.book_generator.generate_initial_concept_for_book(book)
        
        # Parse and save the result
        try:
            book.llm_concept = json.loads(concept_json_string)
        except json.JSONDecodeError:
            # In a real application, we would log this error and
            # potentially return a user-friendly error message.
            # For now, we'll just set it to an empty dict.
            book.llm_concept = {}

        book.status = "active"
        
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)

        return book