import asyncio
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from src.storage.vector_store.base import BaseVectorStore


class ListMetadataInput(BaseModel):
    max_examples: int = Field(
        50,
        ge=1,
        le=500,
        description="Maximum number of example values to return for each metadata field. If the "
                    "total number of unique values exceeds this limit, a warning message will be appended."
    )


class ListMetadataTool(BaseTool):
    name: str = "list_metadata"
    description: str = (
        "List all available metadata fields that can be used for filtering, "
        "along with example values and total counts. Use this to understand what filters are available."
    )
    args_schema: BaseModel = ListMetadataInput
    store: BaseVectorStore

    def _run(self, max_examples: int) -> str:
        metadata = self.store.get_metadata(max_examples)
        if not metadata:
            return "No metadata available."

        lines = []
        for key, info in metadata.items():
            examples = info["examples"]
            total = info["total"]
            examples_str = ", ".join(f"'{e}'" for e in examples)
            if total > max_examples:
                examples_str += f" ... and {total - max_examples} more values"
            lines.append(f"- {key} (total unique values: {total}): {examples_str}")

        return "Available metadata fields:\n" + "\n".join(lines)

    async def _arun(self, max_examples: int) -> str:
        return await asyncio.to_thread(self._run, max_examples)
