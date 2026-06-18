import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from paths.project_paths import ProjectPaths


class NoInput(BaseModel):
    pass


class ListDocumentsTool(BaseTool):
    name: str = "list_documents"
    description: str
    args_schema: type[BaseModel] = NoInput

    def _run(self) -> str:
        paths = ProjectPaths()
        txt_files = sorted(paths.TEXTS.glob("*.txt"))
        if not txt_files:
            return "No .txt files found."

        lines = [f"- {f.name}" for f in txt_files]
        return "Available documents:\n" + "\n".join(lines)

    async def _arun(self):
        return await asyncio.to_thread(self._run)
