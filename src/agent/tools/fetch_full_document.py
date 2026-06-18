import asyncio
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class FetchFullDocumentInput(BaseModel):
    file_path: str = Field(description="Path to the text file of the document (e.g., 'data/processed/autograd.txt')")
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

    def _run(self, file_path: str, max_chars: int = 50000) -> str:
        path = Path(file_path)
        if not path.exists():
            return f"Error: file '{file_path}' not found."
        if path.suffix != ".txt":
            return f"Error: only .txt files are supported, got {path.suffix}"

        text = path.read_text(encoding="utf-8")
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n... [truncated]"
        return text

    async def _arun(self, file_path: str, max_chars: int = 50000):
        return await asyncio.to_thread(self._run, file_path, max_chars)
