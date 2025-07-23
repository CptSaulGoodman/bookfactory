"""AI/LLM integration service."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings


class AIService:
    """Service for AI/LLM interactions."""

    def __init__(self):
        self.model = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )

    def generate_response(self, prompt_text: str) -> str:
        """Generate a response using the AI model."""
        # Since the template is already formatted, we can use it directly
        result = self.model.invoke(prompt_text)
        return result.content 