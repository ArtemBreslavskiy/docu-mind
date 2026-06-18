from pydantic import BaseModel


class ToolConfig(BaseModel):
    name: str
    enable: bool = False
    prompt: str | None = None
