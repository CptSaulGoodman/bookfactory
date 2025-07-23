"""Book generation logic and orchestration."""

from app.services.ai_service import AIService
from app.services.vector_store import VectorStoreService
from app.prompts.templates import get_template
from app.config.settings import (
    DEFAULT_WORLD_PARAMS,
    DEFAULT_STORY_BITS,
    DEFAULT_NUMBER_OF_CHAPTERS,
    DEFAULT_NUMBER_OF_CHARS,
    DEFAULT_NUMBER_OF_MAIN_CHARS,
    DEFAULT_NUMBER_OF_SUPPORT_CHARS,
    DEFAULT_NUMBER_OF_EVENTS
)
from app.models.book import Book
from app.models.character import CharacterCollection


class BookGenerator:
    """Main service for book generation operations."""
    
    def __init__(self):
        self.ai_service = AIService()
        self.vector_store = VectorStoreService()
    
    def generate_initial_concept(
        self,
        number_of_chapters: int = DEFAULT_NUMBER_OF_CHAPTERS,
        world_params: str = DEFAULT_WORLD_PARAMS,
        story_bits: str = DEFAULT_STORY_BITS
    ) -> str:
        """Generate initial book concept."""
        characters_to_use = self.vector_store.get_character_context()
        
        return self.ai_service.generate_response(
            get_template("initial_concept",
                        number_of_chapters=number_of_chapters,
                        world_params=world_params,
                        story_bits=story_bits,
                        characters_to_use=characters_to_use)
        )
    
    def generate_character_sheet(
        self,
        number_of_chars: int = DEFAULT_NUMBER_OF_CHARS,
        number_of_main: int = DEFAULT_NUMBER_OF_MAIN_CHARS,
        number_of_support: int = DEFAULT_NUMBER_OF_SUPPORT_CHARS,
        world_params: str = DEFAULT_WORLD_PARAMS,
        story_bits: str = DEFAULT_STORY_BITS
    ) -> str:
        """Generate character sheets."""
        return self.ai_service.generate_response(
            get_template("character_sheet",
                        number_of_chars=number_of_chars,
                        number_of_main=number_of_main,
                        number_of_support=number_of_support,
                        world_params=world_params,
                        story_bits=story_bits)
        )
    
    def generate_events(
        self,
        chapter_desc: str,
        number_of_events: int = DEFAULT_NUMBER_OF_EVENTS,
        world_params: str = DEFAULT_WORLD_PARAMS,
        story_bits: str = DEFAULT_STORY_BITS
    ) -> str:
        """Generate events for a chapter."""
        characters_to_use = self.vector_store.get_character_context()
        
        return self.ai_service.generate_response(
            get_template("create_events",
                        number_of_events=number_of_events,
                        world_params=world_params,
                        story_bits=story_bits,
                        chapter_desc=chapter_desc,
                        characters_to_use=characters_to_use)
        )
    
    def generate_chapter(
        self,
        chapter: int,
        total_chapters: int,
        chapter_desc: str,
        chapter_events: str,
        world_params: str = DEFAULT_WORLD_PARAMS,
        story_bits: str = DEFAULT_STORY_BITS
    ) -> tuple[str, str]:
        """Generate a complete chapter in two parts."""
        characters_to_use = self.vector_store.get_character_context()
        
        # Generate first part
        part1 = self.ai_service.generate_response(
            get_template("create_chapter_part1",
                        chapter=str(chapter),
                        total_chapters=str(total_chapters),
                        world_params=world_params,
                        story_bits=story_bits,
                        chapter_desc=chapter_desc,
                        characters_to_use=characters_to_use,
                        chapter_events=chapter_events)
        )
        
        # Generate second part
        part2 = self.ai_service.generate_response(
            get_template("create_chapter_part2",
                        chapter=str(chapter),
                        total_chapters=str(total_chapters),
                        world_params=world_params,
                        story_bits=story_bits,
                        chapter_desc=chapter_desc,
                        characters_to_use=characters_to_use,
                        result=part1)
        )
        
        return part1, part2
    
    def setup_characters(self, characters: CharacterCollection) -> None:
        """Setup character embeddings in vector store."""
        self.vector_store.embed_characters(characters) 