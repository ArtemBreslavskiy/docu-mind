import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from retrieval.retriever.base import BaseRetriever


class SearchChunksInput(BaseModel):
    query: str = Field(description="Search query for the documentation (natural language)")
    k: int = Field(5, ge=1, le=30, description="Number of chunks to retrieve")


class SearchChunksTool(BaseTool):
    name: str = "search_chunks"
    description: str
    args_schema: type[BaseModel] = SearchChunksInput
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
