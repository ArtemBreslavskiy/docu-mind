from src.core.retriever.base import BaseRetriever
from src.core.agent.tools.search_chunks import SearchChunksTool
from src.core.agent.tools.search_chunks_by_field import SearchChunksByFieldTool
from src.core.agent.tools.search_chunks_by_json_filter import SearchChunksByJSONFilterTool
from src.core.agent.tools.list_metadata import ListMetadataTool
from src.core.agent.tools.fetch_full_document import FetchFullDocumentTool
from src.core.agent.tools.list_documents import ListDocumentsTool
from src.core.agent.tools.summarize_document import SummarizeDocumentTool
from src.core.agent.tools.ask_clarification import AskClarificationTool
from src.core.models.base import BaseLLMModel


def create_tools(tool_names: list[str], retriever: BaseRetriever, model: BaseLLMModel = None):
    available = {
        "search_chunks": SearchChunksTool(retriever=retriever),
        "search_chunks_by_field": SearchChunksByFieldTool(retriever=retriever),
        "search_chunks_by_json_filter": SearchChunksByJSONFilterTool(retriever=retriever),
        "list_metadata": ListMetadataTool(store=retriever.store),
        "fetch_full_document": FetchFullDocumentTool(),
        "list_documents": ListDocumentsTool(),
        "summarize_document": SummarizeDocumentTool(model=model) if model else None,
        "ask_clarification": AskClarificationTool(),
    }
    tools = []
    for name in tool_names:
        if name in available and available[name] is not None:
            tools.append(available[name])
        else:
            raise ValueError(f"Unknown tool: {name}")
    return tools
