import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from paths.project_paths import ProjectPaths
from src.indexing.documents_stores.base import BaseDocumentsStore


class NoInput(BaseModel):
    pass


class ListDocumentsTool(BaseTool):
    name: str = "list_documents"
    description: str
    args_schema: type[BaseModel] = NoInput
    documents_store: BaseDocumentsStore

    async def _arun(self) -> str:
        docs = await self.documents_store.get_base_info()
        if not docs:
            return "No documents available."

        lines = []
        for doc in docs:
            desc = doc.get("description") or "No description"
            lines.append(f"- ID: {doc['id']}\n  Description: {desc}")

        return "Available documents:\n" + "\n".join(lines)

    def _run(self) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun())
