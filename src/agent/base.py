from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class BaseAgent(ABC):
    @abstractmethod
    def invoke(self, state: dict) -> dict:
        ...

    def run(self, query: str, chat_history: list[BaseMessage] | None = None, **kwargs) -> dict:
        messages = chat_history.copy() if chat_history else []
        messages.append(HumanMessage(content=query))
        state = {"messages": messages, **kwargs}
        new_state = self.invoke(state)
        messages = new_state["messages"]
        last_ai_msg = next(msg for msg in reversed(messages) if isinstance(msg, AIMessage))
        return {
            "output": last_ai_msg if last_ai_msg else "",
            "intermediate_steps": messages,
            "stopped_early": new_state.get("stopped_early", False),
        }
