import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from src.config.loader import load_app_config
from paths.project_paths import ProjectPaths
from src.config.schemas.agent import ToolConfig


class SummarizeDocumentInput(BaseModel):
    text: str = Field(description="The full text to summarize")
    max_length: int = Field(200, ge=100, le=5000, description="Target length of the summary in words")


class SummarizeDocumentTool(BaseTool):
    name: str = "summarize_document"
    description: str
    args_schema: type[BaseModel] = SummarizeDocumentInput
    llm: BaseChatModel

    def _run(self, text: str, max_length: int) -> str:
        paths = ProjectPaths()
        app_config = load_app_config(path=paths.APP_CONFIG)
        system_msg = SystemMessage(
            content=app_config.models.llm.prompts.summarize.format(max_length=max_length, text=text))

        response = self.llm.invoke([system_msg])
        return response.content.strip()

    async def _arun(self, text: str, max_length: int) -> str:
        return await asyncio.to_thread(self._run, text, max_length)
