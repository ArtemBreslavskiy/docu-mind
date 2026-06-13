import asyncio
from langchain.tools import BaseTool
from pydantic import BaseModel
from paths.project_paths import ProjectPaths


class NoInput(BaseModel):
    pass


class ListDocumentsTool(BaseTool):
    name: str = "list_documents"
    description: str = (
        "List all available documents (text files) in the knowledge base. "
        "Use this when you need to know what documents are available or what topics are covered. "
        "This tool takes no arguments."
    )
    args_schema: BaseModel = NoInput

    def _run(self) -> str:
        paths = ProjectPaths()
        txt_files = sorted(paths.TEXTS.glob("*.txt"))
        if not txt_files:
            return "No .txt files found."

        lines = [f"- {f.name}" for f in txt_files]
        return "Available documents:\n" + "\n".join(lines)

    async def _arun(self):
        return await asyncio.to_thread(self._run)
