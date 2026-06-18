from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from retrieval.retriever.base import BaseRetriever
from agent.tools.search_chunks import SearchChunksTool
from agent.tools.search_chunks_by_field import SearchChunksByFieldTool
from agent.tools.search_chunks_by_json_filter import SearchChunksByJSONFilterTool
from agent.tools.list_metadata import ListMetadataTool
from agent.tools.fetch_full_document import FetchFullDocumentTool
from agent.tools.list_documents import ListDocumentsTool
from agent.tools.summarize_document import SummarizeDocumentTool
from agent.tools.ask_clarification import AskClarificationTool
from config.schemas.agent.agent import AgentConfig, ToolConfig


def create_tools(config: AgentConfig, retriever: BaseRetriever, llm: BaseChatModel = None) -> list[BaseTool]:
    config_map = {cfg.name: cfg for cfg in config.tools}

    def _get_config(name: str) -> ToolConfig:
        return config_map.get(name, ToolConfig(name=name, enable=False))

    tool_builders = {
        "search_chunks": lambda cfg: SearchChunksTool(description=cfg.prompt, retriever=retriever),
        "search_chunks_by_field": lambda cfg: SearchChunksByFieldTool(description=cfg.prompt, retriever=retriever),
        "search_chunks_by_json_filter": lambda cfg: SearchChunksByJSONFilterTool(description=cfg.prompt, retriever=retriever),
        "list_metadata": lambda cfg: ListMetadataTool(description=cfg.prompt, store=retriever.store),
        "fetch_full_document": lambda cfg: FetchFullDocumentTool(description=cfg.prompt),
        "list_documents": lambda cfg: ListDocumentsTool(description=cfg.prompt),
        "summarize_document": lambda cfg: SummarizeDocumentTool(description=cfg.prompt, llm=llm) if llm else None,
        "ask_clarification": lambda cfg: AskClarificationTool(description=cfg.prompt),
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
