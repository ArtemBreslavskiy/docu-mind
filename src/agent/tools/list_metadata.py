import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from retrieval.vector_stores.base import BaseVectorStore


class NoInput(BaseModel):
    pass


class ListMetadataTool(BaseTool):
    name: str = "list_metadata"
    description: str
    args_schema: type[BaseModel] = NoInput
    store: BaseVectorStore

    def _run(self) -> str:
        metadata = self.store.list_metadata()
        if not metadata:
            return "No metadata available."

        lines = []
        for key, info in metadata.items():
            examples = info["examples"]
            total = info["total"]
            examples_str = ", ".join(f"'{e}'" for e in examples) + "."
            lines.append(f"- {key} (total unique values: {total}): {examples_str}")

        return "Available metadata fields:\n" + "\n".join(lines)

    async def _arun(self, max_examples: int) -> str:
        return await asyncio.to_thread(self._run, max_examples)
