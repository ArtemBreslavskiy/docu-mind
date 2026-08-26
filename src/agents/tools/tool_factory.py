from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from core.retrievers.base import BaseRetriever
from src.agents.tools.search_chunks import SearchChunksTool
from src.agents.tools.search_chunks_by_field import SearchChunksByFieldTool
from src.agents.tools.search_chunks_by_json_filter import SearchChunksByJSONFilterTool
from src.configs.schemas.agent.agent import AgentConfig, ToolConfig


def create_tools(config: AgentConfig, retriever: BaseRetriever, llm: BaseChatModel = None) -> list[BaseTool]:
    config_map = {cfg.name: cfg for cfg in config.tools}

    def _get_config(name: str) -> ToolConfig:
        return config_map.get(name, ToolConfig(name=name, enable=False))

    tool_builders = {
        "search_chunks": lambda cfg: SearchChunksTool(description=cfg.prompt, retriever=retriever),
        "search_chunks_by_field": lambda cfg: SearchChunksByFieldTool(description=cfg.prompt, retriever=retriever),
        "search_chunks_by_json_filter": lambda cfg: SearchChunksByJSONFilterTool(description=cfg.prompt, retriever=retriever),
    }

    tools = []
    for name, builder in tool_builders.items():
        cfg = _get_config(name)
        if not cfg.enable:
            continue
        tool = builder(cfg)
        if tool is not None:
            tools.append(tool)
    return tools
