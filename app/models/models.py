from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel, Column, JSON


class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = None
    user_prompt: Optional[str] = None
    world_description: Optional[str] = None
    chapters_count: Optional[int] = None
    llm_concept: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    chapters: List["Chapter"] = Relationship(back_populates="book")
    characters: List["Character"] = Relationship(back_populates="book")


class Chapter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_number: int
    title: str
    synopsis: str
    content: Optional[str] = None

    book_id: Optional[int] = Field(default=None, foreign_key="book.id")
    book: Optional[Book] = Relationship(back_populates="chapters")


class Character(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    is_protagonist: bool = False
    
    summary: Optional[str] = None
    profile: Optional[str] = None
    dialogue_voice: Optional[str] = None
    relationships: Optional[str] = None
    role_potential: Optional[str] = None
    story_arc: Optional[str] = None

    book_id: Optional[int] = Field(default=None, foreign_key="book.id")
    book: Optional[Book] = Relationship(back_populates="characters")