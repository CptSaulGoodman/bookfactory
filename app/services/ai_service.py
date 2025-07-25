"""AI/LLM integration service."""

from typing import Optional, Type, TypeVar
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from app import config

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