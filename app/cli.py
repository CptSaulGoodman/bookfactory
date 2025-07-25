# app/cli.py
"""Command-line entry point for the book generation application."""

from app.services.book_generator import BookGenerator
from app.data.sample_data import get_sample_book, get_sample_characters
from app.utils.helpers import print_section, format_chapter_output


def main():
    """Main application entry point."""
    # Initialize services
    book_generator = BookGenerator()
    
    # Get sample data
    sample_book = get_sample_book()
    sample_characters = get_sample_characters()
    
    # Setup character embeddings
    book_generator.setup_characters(sample_characters)
    
    # Example usage - uncomment the function you want to run
    
    # Generate initial concept
    # concept = book_generator.generate_initial_concept()
    # print_section("INITIAL CONCEPT", concept)
    
    # Generate character sheets
    # character_sheets = book_generator.generate_character_sheet()
    # print_section("CHARACTER SHEETS", character_sheets)
    
    # Generate events for chapter 1
    # events = book_generator.generate_events(sample_book.get_chapter("1").synopsis)
    # print_section("CHAPTER EVENTS", events)
    
    # Generate chapter 1
    chapter_1 = sample_book.get_chapter("1")
    part1, part2 = book_generator.generate_chapter(
        chapter=1,
        total_chapters=5,
        chapter_desc=chapter_1.synopsis,
        chapter_events=chapter_1.events[0].description if chapter_1.events else ""
    )
    format_chapter_output(part1, part2)


if __name__ == "__main__":
    main()