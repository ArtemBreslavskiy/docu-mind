import logging
from agents.base import BaseAgent
from agents.implementations.custom_agent import CustomAgent
from llm.factory import create_llm
from configs.schemas.app.app import AppConfig
from configs.schemas.agent.agent import AgentConfig
from retrievers.base import BaseRetriever


def create_agent(
    app_config: AppConfig,
    agent_config: AgentConfig,
    retriever: BaseRetriever,
    logger: logging.Logger = None
) -> BaseAgent:
    llm = create_llm(config=app_config.models)
    return CustomAgent(
        config=agent_config,
        llm=llm,
        retriever=retriever,
        json_parsing=agent_config.json_parsing,
        logger=logger
    )
