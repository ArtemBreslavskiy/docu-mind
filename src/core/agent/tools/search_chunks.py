import asyncio
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from src.core.retriever.base import BaseRetriever


class SearchChunksInput(BaseModel):
    query: str = Field(description="Search query for the documentation (natural language)")
    k: int = Field(5, ge=1, le=30, description="Number of chunks to retrieve")


class SearchChunksTool(BaseTool):
    name: str = "search_documentation"
    description: str = (
        "Search the loaded technical documentation to find information about a "
        "specific topic. Use this whenever you need factual details, definitions, "
        "or explanations that might be covered in the docs."
    )
    args_schema: BaseModel = SearchChunksInput
    retriever: BaseRetriever

    def _run(self, query: str, k: int = 5) -> str:
        results = self.retriever.retrieve(query=query, k=k)
        if not results:
            return "No relevant documents found."

        formatted = []
        for i, res in enumerate(results, 1):
            formatted.append(f"--- Document {i} (score: {res.score:.3f}) --- \n{res.chunk.content}")
        return "\n\n".join(formatted)

    async def _arun(self, query: str, k: int = 5) -> str:
        return await asyncio.to_thread(self._run, query, k)
