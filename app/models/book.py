"""Book data models and structures."""

from typing import Dict, List, Optional
from dataclasses import dataclass


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
    events: Optional[List[Event]] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []


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