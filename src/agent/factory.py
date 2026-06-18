import logging
from agent.base import BaseAgent
from agent.custom_agent import CustomAgent
from llm.llm_factory import create_llm
from config.schemas.app.app import AppConfig
from config.schemas.agent.agent import AgentConfig
from retrieval.retriever.base import BaseRetriever


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
