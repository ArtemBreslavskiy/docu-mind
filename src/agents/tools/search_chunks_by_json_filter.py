import asyncio
import json
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from retrievers.base import BaseRetriever


class SearchChunksByJSONFilterInput(BaseModel):
    query: str = Field(description="Search query text (natural language)")
    filter_json: str = Field(
        description=(
            'JSON string with filtering logic. '
            'Use double quotes for JSON keys and values. Examples:\n'
            '1) Simple AND: {"and": [{"key": "source", "values": ["doc1.txt", "doc2.txt"]}]}\n'
            '2) Simple OR: {"or": [{"key": "author", "values": ["Alice"]}, '
            '{"key": "year", "values": ["2024", "2025"]}]}\n'
            '3) Nested AND+OR: {"and": [{"key": "source", "values": ["autograd.html"]}, '
            '{"or": [{"key": "author", "values": ["Bob"]}, {"key": "status", "values": ["final"]}]}]}\n'
            '4) Multiple fields AND: {"and": [{"key": "source", "values": ["cuda.html"]}, '
            '{"key": "year", "values": ["2026"]}]}\n'
            'Supported operators: "and", "or". Each condition has "key" (field name) and '
            '"values" (array of allowed strings).'
        )
    )
    k: int = Field(5, ge=1, le=30, description="Number of chunks to retrieve after filtering")

    @field_validator("filter_json", mode="before")
    @classmethod
    def coerce_to_string(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v


class SearchChunksByJSONFilterTool(BaseTool):
    name: str = "search_chunks_by_json_filter"
    description: str
    args_schema: type[BaseModel] = SearchChunksByJSONFilterInput
    retriever: BaseRetriever

    def _run(self, query: str, filter_json: str, k: int = 5) -> str:
        try:
            results = self.retriever.retrieve_with_filter(query=query, filter_json=filter_json, k=k)
        except ValueError as e:
            return f"Error: {e}"

        if not results:
            return "No chunks found matching the specified conditions."

        formatted = []
        for i, res in enumerate(results, 1):
            formatted.append(f"--- Chunk {i} (score: {res.score:.3f}) ---\n{res.chunk.content}")
        return "\n\n".join(formatted)

    async def _arun(self, query: str, filter_json: str, k: int = 5) -> str:
        return await asyncio.to_thread(self._run, query, filter_json, k)
