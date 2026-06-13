import asyncio
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class AskClarificationInput(BaseModel):
    question: str = Field(description="The clarification question to ask the user")


class AskClarificationTool(BaseTool):
    name: str = "ask_clarification"
    description: str = (
        "Ask the user a clarifying question when the original query is ambiguous or needs more detail. "
        "Use this only when absolutely necessary."
    )
    args_schema: BaseModel = AskClarificationInput

    def _run(self, question: str) -> str:
        return f"CLARIFICATION: {question}"

    async def _arun(self, question: str) -> str:
        return await asyncio.to_thread(self._run)
