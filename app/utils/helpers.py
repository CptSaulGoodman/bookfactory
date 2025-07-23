"""Utility functions for the application."""

from typing import Any


def print_section(title: str, content: Any) -> None:
    """Print a formatted section with title and content."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(content)
    print(f"{'='*50}\n")


def format_chapter_output(part1: str, part2: str) -> None:
    """Format and print chapter output."""
    print_section("CHAPTER PART 1", part1)
    print_section("CHAPTER PART 2", part2) 