from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    max_iterations: int = Field(5, ge=1, le=20)
    tools: list[str] = ["search_chunks"]