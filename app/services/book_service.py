# app/services/book_service.py
import json
from typing import List, Optional
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from app.models.models import Book, Character, Chapter
from app.services.ai_service import AIService
from app.services.book_generator import BookGenerator
from app.prompts.templates import get_template
import logging

class BookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Instantiate AIService and BookGenerator
        self.ai_service = AIService()
        self.book_generator = BookGenerator(ai_service=self.ai_service)

    async def _create_chapters_from_concept(self, book: "Book") -> None:
        """
        Creates Chapter objects from the book's LLM concept data.
        This is a helper method for just-in-time chapter creation.
        """
        # Get the chapter list from the book's LLM concept
        chapters_data = book.llm_concept.get("chapters", [])
        
        # Create Chapter objects for each conceptual chapter
        for chapter_data in chapters_data:
            chapter = Chapter(
                chapter_number=chapter_data.get("chapter_number", 1),
                title=chapter_data.get("chapter_title", "Untitled Chapter"),
                synopsis=chapter_data.get("chapter_synopsis", ""),
                status="draft",
                book_id=book.id
            )
            self.session.add(chapter)
        
        # Commit all the new chapters to the database
        await self.session.commit()

    async def get_book(self, book_id: int) -> "Book":
        """
        Retrieves a book by its ID.
        """
        logging.info(f"Retrieving book {book_id}")
        
        try:
            query = select(Book).where(Book.id == book_id).options(
                selectinload(Book.characters),
                selectinload(Book.chapters)
            )
            result = await self.session.execute(query)
            book = result.scalar_one_or_none()
            
            if not book:
                logging.error(f"Book with ID {book_id} not found")
                raise ValueError(f"Book with ID {book_id} not found.")
            
            logging.info(f"Retrieved book {book_id} with {len(book.chapters)} chapters and {len(book.characters)} characters")
            
            # Check if we need to create chapters from the concept
            if book and book.llm_concept and not book.chapters:
                logging.info(f"Creating chapters from concept for book {book_id}")
                # Create chapters from the concept data
                await self._create_chapters_from_concept(book)
                
                # Re-fetch the book to load the newly created chapters relationship
                query = select(Book).where(Book.id == book_id).options(
                    selectinload(Book.characters),
                    selectinload(Book.chapters)
                )
                result = await self.session.execute(query)
                book = result.scalar_one_or_none()
                logging.info(f"Re-fetched book {book_id} after creating chapters")
            
            return book
            
        except Exception as e:
            logging.error(f"Error retrieving book {book_id}: {e}", exc_info=True)
            raise

    async def get_books(self, statuses: Optional[List[str]] = None) -> List[Book]:
        """
        Retrieves books, optionally filtered by status, ordered by creation date.
        """
        query = select(Book).options(
            selectinload(Book.characters),
            selectinload(Book.chapters)
        ).order_by(Book.created_at.desc())
        if statuses:
            if "draft" in statuses:
                statuses.append("failed")
            query = query.where(Book.status.in_(statuses))
        
        result = await self.session.execute(query)
        books = result.scalars().all()
        return books

    async def delete_book(self, book_id: int) -> None:
        """
        Deletes a book by its ID.
        """
        book = await self.get_book(book_id)
        logging.info(f"Deleting book {book_id}")
        if book:
            await self.session.delete(book)
            await self.session.commit()
            logging.info(f"Deleted book {book_id}")
        else:
            logging.error(f"Book {book_id} not found")

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

    async def update_book_status(self, book_id: int, status: str) -> Book:
        """
        Updates the status of a book.
        """
        book = await self.get_book(book_id)
        book.status = status
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

        # Create Chapter objects from the LLM concept and persist them to the database
        for chapter_data in llm_concept.chapters:
            chapter = Chapter(
                chapter_number=chapter_data.chapter_number,
                title=chapter_data.chapter_title,
                synopsis=chapter_data.chapter_synopsis,
                book_id=book.id
            )
            self.session.add(chapter)

        book.status = "active"
        
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)

        return book

    async def initiate_chapter_writing(self, chapter_id: int, user_directives: str = "") -> Chapter:
        """
        Initiates the chapter writing process by updating the chapter status to 'writing'
        and saving any user directives.
        """
        # Query the chapter by ID
        query = select(Chapter).where(Chapter.id == chapter_id)
        result = await self.session.execute(query)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise ValueError(f"Chapter with ID {chapter_id} not found.")
        
        # Update chapter status and save user directives
        chapter.status = "writing"
        chapter.user_directives = user_directives
        
        self.session.add(chapter)
        await self.session.commit()
        await self.session.refresh(chapter)
        
        return chapter

    async def build_chapter_prompt(self, chapter: Chapter, part: int, user_directives: str) -> str:
        """Builds the prompt for chapter generation."""
        logging.info(f"Building chapter prompt for chapter {chapter.id}, part {part}")
        
        try:
            book = await self.get_book(chapter.book_id)
            logging.info(f"Retrieved book {book.id} for chapter {chapter.id}")

            # Get character context
            characters_to_use = ""
            if book.characters:
                character_descriptions = [
                    f"<name>{char.name}</name>"
                    + f"<role>{'protagonist' if char.is_protagonist else 'supporting'}</role>"
                    + f"<summary>{char.description}</summary>"
                    + f"<dialogue_voice>{char.dialogue_voice}</dialogue_voice>"
                    + f"<relationships>{char.relationships}</relationships>"
                    + f"<role_potential>{char.role_potential}</role_potential>"
                    + f"<story_arc>{char.story_arc}</story_arc>"
                    for char in book.characters
                ]
                characters_to_use = "\n".join(character_descriptions)
                logging.info(f"Found {len(book.characters)} characters for chapter {chapter.id}")

            # Get chapter events from the stored concept
            chapter_events = ""
            if book.llm_concept:
                try:
                    concept_data = book.llm_concept
                    if isinstance(book.llm_concept, str):
                        concept_data = json.loads(book.llm_concept)
                    
                    if "chapters" in concept_data:
                        for chapter_data in concept_data["chapters"]:
                            if chapter_data.get("chapter_number") == chapter.chapter_number:
                                events = chapter_data.get("chapter_events", [])
                                if events:
                                    event_descriptions = [f"• {event.get('event_title', '')}: {event.get('event_description', '')}" for event in events]
                                    chapter_events = "\n".join(event_descriptions)
                                    logging.info(f"Found {len(events)} events for chapter {chapter.id}")
                                break
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logging.warning(f"Error parsing chapter events for chapter {chapter.id}: {e}")
                    chapter_events = ""

            rag_retrieved_context = ""
            previous_chapter_ending = ""

            if chapter.chapter_number > 1:
                previous_chapter_number = chapter.chapter_number - 1
                for ch in book.chapters:
                    if ch.chapter_number == previous_chapter_number:
                        rag_retrieved_context = ch.previous_storyline
                        previous_chapter_content = ch.content
                        previous_chapter_ending = previous_chapter_content.split("-----")[1].strip()
                        break

            template_name = f"create_chapter_part{part}"
            prompt_params = {
                "chapter": str(chapter.chapter_number),
                "title": chapter.title,
                "total_chapters": str(len(book.chapters)),
                
                "world_params": book.world_description,
                "story_bits": book.user_prompt,
                "chapter_desc": chapter.synopsis,
                "characters_to_use": characters_to_use,
                "chapter_events": chapter_events,
                
                "rag_retrieved_context": rag_retrieved_context,
                "user_directives": user_directives,
            }
            
            if part == 2:
                prompt_params["previous_part_content"] = chapter.content # Pass Part 1 content
            else:
                prompt_params["previous_chapter_ending"] = previous_chapter_ending

            prompt = get_template(template_name, **prompt_params)
            
            logging.info(f"Successfully built prompt for chapter {chapter.id}, part {part}")
            logging.info(f"Prompt: {prompt}")
            return prompt
            
        except Exception as e:
            logging.error(f"Error building chapter prompt for chapter {chapter.id}: {e}", exc_info=True)
            raise