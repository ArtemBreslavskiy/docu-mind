import logging
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, ToolMessage
from agent.base import BaseAgent
from src.logger.logger_setup import get_logger
from retrieval.retriever.base import BaseRetriever
from config.schemas.agent.agent import AgentConfig
from agent.tools.tool_factory import create_tools
from agent.json_parse_tool_calls import parse_tool_calls_from_text


class CustomAgent(BaseAgent):
    def __init__(
        self,
        llm: BaseChatModel,
        retriever: BaseRetriever,
        max_iterations: int = 5,
        json_parsing: bool = False,
        logger: logging.Logger = None,
    ):
        self.logger = logger if logger is not None else get_logger("agent")
        if logger is None:
            self.logger.disabled = True

        self.retriever = retriever
        self.json_parsing = json_parsing
        self.max_iterations = max_iterations

        self.tools = create_tools(config=self.config, retriever=retriever, llm=llm)
        self.llm = llm.bind_tools(self.tools)
        self.tool_map = {tool.name: tool for tool in self.tools}

    def invoke(self, state: dict) -> dict:
        messages = state["messages"]
        max_iterations = state.get("max_iterations", self.max_iterations)

        self.logger.info("Agent invoked with %d initial messages, max_steps=%d", len(messages), max_iterations)

        for iteration in range(1, max_iterations + 1):
            self.logger.info("=== Step %d/%d ===", iteration, max_iterations)

            response = self.llm.invoke(messages)
            messages.append(response)
            tool_calls = response.tool_calls

            if not tool_calls and self.json_parsing and response.content:
                tool_calls = parse_tool_calls_from_text(response.content)
                if tool_calls:
                    self.logger.info("Parsed %d tool call(s) from text response.", len(tool_calls))
                    response.content = ""

            if response.content:
                snippet = f"{response.content[:200]}..." if len(response.content) > 200 else response.content
                self.logger.debug("LLM content: %s", snippet)

            if tool_calls:
                tool_names_str = ", ".join([tool_call['name'] for tool_call in tool_calls]) + "."
                self.logger.info(
                    "LLM requested %d tool call(s): %s",
                    len(tool_calls),
                    tool_names_str
                )
            else:
                self.logger.info("No tool calls, final answer received.")
                break

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                self.logger.info("Executing tool '%s' with args %s", tool_name, tool_args)
                result = str(self._execute_tool(tool_name, tool_args))
                snippet = f"{result[:200]}..." if len(result) > 200 else result
                self.logger.info("Tool '%s' returned: %s", tool_name, snippet)
                messages.append(ToolMessage(content=result, tool_call_id=tool_id))

            if iteration == max_iterations:
                self.logger.warning("Reached max_steps (%d), requesting final summary from LLM.",
                                    max_iterations)

                messages.append(HumanMessage(content=self.config.prompts.max_steps_reached))
                final_response = self.llm.invoke(messages)
                snippet = f"{final_response.content[:200]}..." \
                    if len(final_response.content) > 200 else final_response.content
                self.logger.info("Final summary received after step limit. Content: %s", snippet)
                break

        new_state = state.copy()
        new_state["messages"] = messages
        new_state["stopped_early"] = (iteration == max_iterations)
        return new_state

    def _execute_tool(self, tool_name: str, tool_args: dict):
        if tool_name not in self.tool_map:
            self.logger.error("Error: tool '%s' not found.", tool_name)
            return f"Error: tool '{tool_name}' not found."

        try:
            result = self.tool_map[tool_name].invoke(tool_args)
            return str(result)
        except Exception as ex:
            msg = f"Error executing tool '{tool_name}': {ex}"
            self.logger.error(msg)
            return msg
