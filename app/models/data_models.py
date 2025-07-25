# app/models/data_models.py
"""Legacy data models for CLI and stateless generation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

@dataclass
class Event:
    """Represents an event within a chapter."""
    title: str
    description: str


@dataclass
class Chapter:
    """Represents a chapter in a book."""
    title: str
    synopsis: str
    events: List[Event] = field(default_factory=list)


@dataclass
class Book:
    """Represents a complete book structure."""
    book_title: str
    chapters: Dict[str, Chapter]

    def get_chapter(self, chapter_number: str) -> Optional[Chapter]:
        """Get a specific chapter by number."""
        return self.chapters.get(chapter_number)

    def add_chapter(self, chapter_number: str, chapter: Chapter) -> None:
        """Add a new chapter to the book."""
        self.chapters[chapter_number] = chapter


@dataclass
class Character:
    """Represents a character in the book."""
    name: str
    main_character: bool
    role: str
    summary: str


@dataclass
class CharacterCollection:
    """Collection of characters for a book."""
    chars: List[Character]

    def get_main_characters(self) -> List[Character]:
        """Get all main characters."""
        return [char for char in self.chars if char.main_character]

    def get_supporting_characters(self) -> List[Character]:
        """Get all supporting characters."""
        return [char for char in self.chars if not char.main_character]

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get a character by name."""
        for char in self.chars:
            if char.name == name:
                return char
        return None

class BookChapterEvent(BaseModel):
    """Pydantic model for a book chapter event."""
    event_title: str
    event_description: str

class BookChapter(BaseModel):
    """Pydantic model for a book chapter."""
    chapter_number: int
    chapter_title: str
    chapter_synopsis: str = Field(description="A brief synopsis of the chapter - making curious but without giving too much away.")
    chapter_events: List[BookChapterEvent] = Field(description="A list of events that will happen in the chapter more detailed than the synopsis.")

class BookConcept(BaseModel):
    """Pydantic model for the structured LLM concept output."""
    title: str
    premise: str
    chapters: List[BookChapter]