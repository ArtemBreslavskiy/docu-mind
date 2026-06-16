from pydantic import BaseModel, Field


class AgentPromptsConfig(BaseModel):
    system: str = (
        "You are a documentation bot.You have NO knowledge of your own. "
        "The ONLY way to answer questions is to call the `search_chunks` tool. "
        "If you answer without calling it, you will be penalized.Before every response, "
        "output a call to `search_chunks` with the user's question."
    )
    max_steps_reached: str = (
        "You have reached the maximum number of tool calls. "
        "Based on all the information gathered so far, please provide a final answer. "
        "Do not request any more tools."
    )


class ToolConfig(BaseModel):
    name: str
    enable: bool = False
    prompt: str | None = None


class AgentConfig(BaseModel):
    max_iterations: int = Field(5, ge=1, le=20)
    json_parsing: bool = False
    tools: list[ToolConfig] = Field(default_factory=list[ToolConfig])
    prompts: AgentPromptsConfig = Field(default_factory=AgentPromptsConfig)
