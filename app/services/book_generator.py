"""Book generation logic and orchestration."""

import json
from typing import AsyncGenerator, TYPE_CHECKING
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.ai_service import AIService
from app.services.vector_store import VectorStoreService
from app.prompts.templates import get_template
from app import config
from app.models.data_models import BookConcept, CharacterCollection
from app.models.models import Book, Character, Chapter

if TYPE_CHECKING:
    from app.services.book_service import BookService


class BookGenerator:
    """Main service for book generation operations."""
    
    def __init__(self, ai_service: AIService = None):
        self.ai_service = ai_service if ai_service else AIService()
        self.vector_store = VectorStoreService()
    
    async def generate_initial_concept(
        self,
        number_of_chapters: int = config.DEFAULT_NUMBER_OF_CHAPTERS,
        world_params: str = config.DEFAULT_WORLD_PARAMS,
        story_bits: str = config.DEFAULT_STORY_BITS
    ) -> str:
        """Generate initial book concept."""
        characters_to_use = self.vector_store.get_character_context()
        
        return await self.ai_service.generate_response(
            get_template("initial_concept",
                        number_of_chapters=number_of_chapters,
                        world_params=world_params,
                        story_bits=story_bits,
                        characters_to_use=characters_to_use)
        )
    
    async def generate_initial_concept_for_book(self, book: Book) -> BookConcept:
        """Generate initial book concept from a Book model."""
        # Extract character information from the book model
        characters_to_use = ""
        if book.characters:
            character_descriptions = []
            for character in book.characters:
                char_type = "protagonist" if character.is_protagonist else "supporting"
                character_descriptions.append(
                    f"name: {character.name}, role: {char_type}, summary: {character.description}"
                )
            characters_to_use = "\n".join(character_descriptions)
        
        prompt = get_template("initial_concept",
                                number_of_chapters=book.chapters_count,
                                world_params=book.world_description,
                                story_bits=book.user_prompt,
                                characters_to_use=characters_to_use)

        return await self.ai_service.generate_response(prompt, model=BookConcept)

    async def generate_character_sheet(
        self,
        character: Character,
        world_params: str = config.DEFAULT_WORLD_PARAMS,
        story_bits: str = config.DEFAULT_STORY_BITS
    ) -> str:
        """Generate character sheets."""
        prompt = get_template("character_sheet",
                        character_name=character.name,
                        basic_traits=character.description,
                        is_protagonist=character.is_protagonist,
                        world_params=world_params,
                        story_bits=story_bits)
        return await self.ai_service.generate_response(prompt, model=Character)
    
    async def generate_events(
        self,
        chapter_desc: str,
        number_of_events: int = config.DEFAULT_NUMBER_OF_EVENTS,
        world_params: str = config.DEFAULT_WORLD_PARAMS,
        story_bits: str = config.DEFAULT_STORY_BITS
    ) -> str:
        """Generate events for a chapter."""
        characters_to_use = self.vector_store.get_character_context()
        
        return await self.ai_service.generate_response(
            get_template("create_events",
                        number_of_events=number_of_events,
                        world_params=world_params,
                        story_bits=story_bits,
                        chapter_desc=chapter_desc,
                        characters_to_use=characters_to_use)
        )
    
    # Commenting out the old generate_chapter method
    # async def generate_chapter(
    #     self,
    #     chapter: int,
    #     total_chapters: int,
    #     chapter_desc: str,
    #     chapter_events: str,
    #     world_params: str = config.DEFAULT_WORLD_PARAMS,
    #     story_bits: str = config.DEFAULT_STORY_BITS
    # ) -> tuple[str, str]:
    #     """Generate a complete chapter in two parts."""
    #     characters_to_use = self.vector_store.get_character_context()
        
    #     # Generate first part
    #     part1 = await self.ai_service.generate_response(
    #         get_template("create_chapter_part1",
    #                     chapter=str(chapter),
    #                     total_chapters=str(total_chapters),
    #                     world_params=world_params,
    #                     story_bits=story_bits,
    #                     chapter_desc=chapter_desc,
    #                     characters_to_use=characters_to_use,
    #                     chapter_events=chapter_events)
    #     )
        
    #     # Generate second part
    #     part2 = await self.ai_service.generate_response(
    #         get_template("create_chapter_part2",
    #                     chapter=str(chapter),
    #                     total_chapters=str(total_chapters),
    #                     world_params=world_params,
    #                     story_bits=story_bits,
    #                     chapter_desc=chapter_desc,
    #                     characters_to_use=characters_to_use,
    #                     result=part1)
    #     )
        
    #     return part1, part2
    
    
    def setup_characters(self, characters: CharacterCollection) -> None:
        """Setup character embeddings in vector store."""
        self.vector_store.embed_characters(characters)