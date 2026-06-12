import asyncio
from pathlib import Path
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from paths.project_paths import ProjectPaths


class FetchFullDocumentInput(BaseModel):
    file_path: str = Field(description="Path to the text file of the document (e.g., 'data/processed/autograd.txt')")
    max_chars: int = Field(
        50000,
        ge=1000,
        le=500000,
        description="Maximum number of characters to return (to avoid too much context)"
    )


class FetchFullDocument(BaseTool):
    name: str = "fetch_full_document"
    description: str = (
        "Retrieve the full text of a document from a text file. "
        "Use this when the chunks from search_documentation are insufficient, "
        "or when you need the complete context of a specific file. "
        "The file_path should come from the 'txt_path' metadata of a search result."
    )
    args_schema: BaseModel = FetchFullDocumentInput

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
