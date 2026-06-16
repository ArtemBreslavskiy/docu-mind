import logging
from src.core.agent.base import BaseAgent
from src.core.agent.custom_agent import CustomAgent
from src.core.llm.llm_factory import create_llm
from src.config.schemas.app import AppConfig
from src.config.schemas.agent import AgentConfig
from src.core.retriever.base import BaseRetriever


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
