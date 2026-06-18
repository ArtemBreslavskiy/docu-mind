from pydantic import BaseModel, Field
from typing import Union
from src.config.schemas.agent.tool import ToolConfig
from src.config.schemas.agent.prompts import PromptsConfig
from src.config.schemas.agent.agent_init import CustomAgentInitConfig


class AgentConfig(BaseModel):
    tools: list[ToolConfig] = Field(default_factory=list[ToolConfig])
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    init: Union[CustomAgentInitConfig] = (Field(discriminator="type"))
