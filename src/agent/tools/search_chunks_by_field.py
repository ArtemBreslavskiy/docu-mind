import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from retrieval.retriever.base import BaseRetriever


class SearchChunksByFieldInput(BaseModel):
    query: str = Field(description="Search query for the documentation (natural language)")
    filter_key: str = Field(description="Metadata field to filter on (e.g., 'source')")
    filter_value: str = Field(description="Exact value of the metadata field to match. Example: if filter_key "
                                          "is 'source', a valid filter_value would be 'autograd.html'.")
    k: int = Field(5, ge=1, le=30, description="Number of chunks to retrieve after filtering")


class SearchChunksByFieldTool(BaseTool):
    name: str = "search_chunks_by_field"
    description: str
    args_schema: type[BaseModel] = SearchChunksByFieldInput
    retriever: BaseRetriever

    def _run(self, query: str, filter_key: str, filter_value: str, k: int = 5) -> str:
        try:
            results = self.retriever.retrieve_with_filter(
                query=query,
                filter_key=filter_key,
                filter_value=filter_value,
                k=k
            )
        except ValueError as ex:
            return f"Error: {ex}"

        if not results:
            return f"No chunks found with {filter_key}='{filter_value}'."

        formatted = []
        for i, res in enumerate(results, 1):
            formatted.append(f"--- Chunk {i} (score: {res.score:.3f}) ---\n{res.chunk.content}")
        return "\n\n".join(formatted)

    async def _arun(self, query: str, filter_key: str, filter_value: str, k: int = 5) -> str:
        return await asyncio.to_thread(self._run, query, filter_key, filter_value, k)
