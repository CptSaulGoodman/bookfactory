# app/services/book_service.py
import json
from typing import List, Optional
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from app.models.models import Book, Character
from app.services.ai_service import AIService
from app.services.book_generator import BookGenerator

class BookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Instantiate AIService and BookGenerator
        self.ai_service = AIService()
        self.book_generator = BookGenerator(ai_service=self.ai_service)

    async def get_book(self, book_id: int) -> "Book":
        """
        Retrievis a book by its ID.
        """
        query = select(Book).where(Book.id == book_id).options(
            selectinload(Book.characters),
            selectinload(Book.chapters)
        )
        result = await self.session.execute(query)
        book = result.scalar_one_or_none()
        if not book:
            # In a real app, a more specific exception would be better.
            raise ValueError(f"Book with ID {book_id} not found.")
        return book

    async def get_books(self, statuses: Optional[List[str]] = None) -> List[Book]:
        """
        Retrieves books, optionally filtered by status, ordered by creation date.
        """
        query = select(Book).options(
            selectinload(Book.characters),
            selectinload(Book.chapters)
        ).order_by(Book.created_at.desc())
        if statuses:
            query = query.where(Book.status.in_(statuses))
        
        result = await self.session.execute(query)
        books = result.scalars().all()
        return books

    async def delete_book(self, book_id: int) -> None:
        """
        Deletes a book by its ID.
        """
        book = await self.get_book(book_id)
        if book:
            self.session.delete(book)
            await self.session.commit()

    async def create_book_draft(self, user_prompt: str) -> Book:
        """
        Creates a new Book instance with a 'draft' status.
        """
        book = Book(user_prompt=user_prompt, status="draft")
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def update_book(self, book_id: int, **kwargs) -> Book:
        """
        Updates a book with the given attributes.
        """
        book = await self.get_book(book_id)
        for key, value in kwargs.items():
            if hasattr(book, key) and value is not None:
                setattr(book, key, value)
        
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def save_characters_for_book(self, book_id: int, characters_data: list[dict]) -> None:
        """
        Saves character data for a specific book.
        """
        # Delete all existing characters for the book using proper SQLAlchemy delete
        delete_query = delete(Character).where(Character.book_id == book_id)
        await self.session.execute(delete_query)
        await self.session.commit()  # Commit the deletions first
        
        # Clear the session to remove references to deleted objects
        self.session.expunge_all()

        # Re-fetch the book after deletion to get a clean state
        book = await self.get_book(book_id)
        
        # Simple validation: Ensure only one protagonist
        protagonist_count = sum(1 for char in characters_data if char.get('is_protagonist'))
        if protagonist_count != 1:
            raise ValueError("There must be exactly one protagonist.")

        for char_data in characters_data:
            character = Character(
                name=char_data['name'],
                description=char_data['description'],
                is_protagonist=char_data.get('is_protagonist', False),
                book_id=book.id,
                summary=char_data.get('summary', None),
                profile=char_data.get('profile', None),
                dialogue_voice=char_data.get('dialogue_voice', None),
                relationships=char_data.get('relationships', None),
                role_potential=char_data.get('role_potential', None),
                story_arc=char_data.get('story_arc', None)
            )
            self.session.add(character)
        
        await self.session.commit()

    async def finalize_and_generate_book(self, book_id: int) -> Book:
        """
        Marks the book as 'active' and triggers the generation process.
        """
        book = await self.get_book(book_id)

        characters_data = []
        characters = book.characters
        for character in characters:
            print(f"Generating character sheet for {character.name}")
            character_sheet = await self.book_generator.generate_character_sheet(character, book.world_description, book.user_prompt)
            llm_character_sheet = character_sheet.dict()
            print(f"Character sheet for {character.name}: {llm_character_sheet}")
            characters_data.append(llm_character_sheet)
        
        await self.save_characters_for_book(book_id=book_id, characters_data=characters_data)
        
        # After saving the characters, the book object in memory is stale.
        # We re-fetch it from the database to get the updated characters
        # before passing it to the next function.
        book = await self.get_book(book_id)

        llm_concept = await self.book_generator.generate_initial_concept_for_book(book)
        
        # Convert the Pydantic BookConcept model to a dictionary for database storage
        # The llm_concept is a BookConcept Pydantic model from data_models.py that contains
        # structured LLM output. We convert it to a dict to store in the Book SQLModel's
        # llm_concept JSON field for database persistence.
        book.llm_concept = llm_concept.dict()

        book.status = "active"
        
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)

        return book