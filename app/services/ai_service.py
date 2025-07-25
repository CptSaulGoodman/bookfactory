"""AI/LLM integration service."""

from typing import Optional, Type, TypeVar
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app import config
from app.prompts.templates import get_template

T = TypeVar("T", bound=BaseModel)


class AIService:
    """Service for AI/LLM interactions."""

    def __init__(self):
        self.model = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=0,
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_API_BASE,
        )

    def generate_response(self, prompt_text: str, model: Optional[Type[T]] = None) -> T | str:
        """
        Generate a response using the AI model, with optional structured output.
        """
        if model:
            structured_llm = self.model.with_structured_output(model)
            result = structured_llm.invoke(prompt_text)
            return result
        else:
            result = self.model.invoke(prompt_text)
            return result.content

    def generate_comment(self, user_story_idea: str,
            user_book_title: str = "Not defined yet", 
            user_world_description: str = "Not defined yet", 
            user_characters: str = "Not defined yet") -> str:
        """Generate a funny comment based on user input."""
        prompt = get_template("funny_comment", 
            user_story_idea=user_story_idea, 
            user_book_title=user_book_title, 
            user_world_description=user_world_description, 
            user_characters=user_characters )
        return self.generate_response(prompt)

    def generate_suggestion(self, context: str, field_name: str) -> str:
        """Generate a creative suggestion for a field."""
        prompt = get_template("field_suggestion", context=context, field_name=field_name)
        return self.generate_response(prompt)