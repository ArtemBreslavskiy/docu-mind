import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from src.indexing.documents_stores.base import BaseDocumentsStore


class FetchFullDocumentInput(BaseModel):
    doc_id: str = Field(description="ID of the document to retrieve")
    max_chars: int = Field(
        50000,
        ge=1000,
        le=500000,
        description="Maximum number of characters to return (to avoid too much context)"
    )


class FetchFullDocumentTool(BaseTool):
    name: str = "fetch_full_document"
    description: str
    args_schema: type[BaseModel] = FetchFullDocumentInput
    documents_store: BaseDocumentsStore

    async def _arun(self, doc_id: str, max_chars: int = 50000) -> str:
        doc = await self.documents_store.get(doc_id)
        if doc is None:
            return f"Error: document with ID '{doc_id}' not found."

        text = doc.content
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n... [truncated]"
        return text

    def _run(self, doc_id: str, max_chars: int = 50000) -> str:
        return asyncio.run(self._arun(doc_id, max_chars))
