import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class AskClarificationInput(BaseModel):
    question: str = Field(description="The clarification question to ask the user")


class AskClarificationTool(BaseTool):
    name: str = "ask_clarification"
    description: str
    args_schema: type[BaseModel] = AskClarificationInput

    def _run(self, question: str) -> str:
        return f"CLARIFICATION: {question}"

    async def _arun(self, question: str) -> str:
        return await asyncio.to_thread(self._run)
