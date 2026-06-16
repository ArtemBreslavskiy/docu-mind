import uuid
import ollama
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import Field


class OllamaChatModel(BaseChatModel):
    model: str
    temperature: float
    max_tokens: int
    base_url: str = "http://localhost:11434"
    client: ollama.Client = Field(None, exclude=True)
    _bound_tools: Optional[list] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.client = ollama.Client(host=self.base_url)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        ollama_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, ToolMessage):
                role = "tool"
            else:
                role = "assistant"
            ollama_messages.append({"role": role, "content": msg.content})

        response = self.client.chat(
            model=self.model,
            messages=ollama_messages,
            options={
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
            tools=self._bound_tools,
        )

        response_msg = response.message
        content = response_msg.content or ""
        tool_calls_data = response_msg.tool_calls or []

        tool_calls = []
        for tool_call in tool_calls_data:
            call_id = getattr(tool_call, "id", None) or str(uuid.uuid4())
            tool_calls.append({
                "id": call_id,
                "name": tool_call.function.name,
                "args": tool_call.function.arguments
            })

        ai_msg = AIMessage(
            content=content,
            tool_calls=tool_calls
        )
        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    def bind_tools(self, tools: list, **kwargs: Any) -> "OllamaChatModel":
        self._bound_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.args_schema.schema(),
                },
            }
            for t in tools
        ]

        return self

    @property
    def _llm_type(self) -> str:
        return "ollama_chat"
