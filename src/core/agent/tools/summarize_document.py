import asyncio
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from src.core.models.models_factory import create_model
from src.config.loader import load_app_config
from paths.project_paths import ProjectPaths


class SummarizeDocumentInput(BaseModel):
    text: str = Field(description="The full text to summarize")
    max_length: int = Field(200, ge=100, le=5000, description="Target length of the summary in words")


class SummarizeDocumentTool(BaseTool):
    name: str = "summarize_document"
    description: str = (
        "Summarize a long document into a shorter version while preserving key facts. "
        "Use this when a document is too large to fit into context or when the user asks for a summary."
    )
    args_schema: BaseModel = SummarizeDocumentInput

    def _run(self, text: str, max_length: int) -> str:
        paths = ProjectPaths()
        app_config = load_app_config(path=paths.APP_CONFIG)
        model = create_model(app_config.models.llm.get_summarize_config())

        return model.summarize(text=text, max_length=max_length)

    async def _arun(self, text: str, max_length: int) -> str:
        return await asyncio.to_thread(self._run, text, max_length)
