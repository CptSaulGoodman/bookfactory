"""Character data models and structures."""

from dataclasses import dataclass
from typing import List


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
    
    def get_character_by_name(self, name: str) -> Character:
        """Get a character by name."""
        for char in self.chars:
            if char.name == name:
                return char
        raise ValueError(f"Character '{name}' not found") 