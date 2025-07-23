"""Vector database operations for character storage and retrieval."""

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.models.character import CharacterCollection


class VectorStoreService:
    """Service for managing character embeddings and retrieval."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        self.vector_store = Chroma(
            collection_name=settings.COLLECTION_NAME,
            persist_directory=settings.DB_LOCATION,
            embedding_function=self.embeddings,
        )
    
    def embed_characters(self, characters: CharacterCollection) -> None:
        """Embed characters into the vector store."""
        documents = []
        ids = []
        
        for i, char in enumerate(characters.chars):
            document = Document(
                page_content=f"name: {char.name}, role:{char.role} summary:{char.summary}",
                metadata={"name": char.name, "role": char.role},
                id=str(i)
            )
            ids.append(str(i))
            documents.append(document)
        
        self.vector_store.add_documents(documents=documents, ids=ids)
    
    def get_character_context(self, query: str = "Tell me more about the persons in this book") -> str:
        """Retrieve character context for AI prompts."""
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": settings.RETRIEVER_K}
        )
        docs = retriever.invoke(query)
        return "\n".join([doc.page_content for doc in docs])