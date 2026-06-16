from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, SystemMessage
from paths.project_paths import ProjectPaths
from src.config.loader import load_app_config, load_agent_config, load_pipeline_config
from src.core.embedder.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.storage.vector_store.store_factory import create_vector_store
from src.core.retriever.retriever_factory import create_retriever
from src.core.agent.agent_factory import create_agent
from src.logger.logger_setup import get_logger


def query_agent():
    load_dotenv()

    paths = ProjectPaths()
    app_config = load_app_config(path=paths.APP_CONFIG)
    pipeline_config = load_pipeline_config(path=paths.PIPELINE_CONFIG)
    agent_config = load_agent_config(path=paths.AGENT_CONFIG)

    embedder = SentenceTransformerEmbedder(config=app_config.models.embedding)
    store = create_vector_store(config=app_config.data.storage)
    retriever = create_retriever(config=pipeline_config.retriever, embedder=embedder, store=store)
    logger = get_logger("agent")
    agent = create_agent(app_config=app_config, agent_config=agent_config, retriever=retriever, logger=logger)

    chat_history: list[BaseMessage] = [SystemMessage(content=agent_config.prompts.system)]
    print("=== DocuMind Agent ===")
    while True:
        user_input = input("\nEnter a question (or 'exit' to exit): ")
        if user_input.lower() == "exit":
            break

        result = agent.run(query=user_input, chat_history=chat_history)
        output = result["output"]
        output = output.content

        while output.startswith("CLARIFICATION:"):
            question = output.replace("CLARIFICATION:", "").strip()
            print(f"Assistant: {question}")
            clarification = input("You: ")

            chat_history.append(HumanMessage(content=clarification))
            chat_history.append(AIMessage(content=output))

            result = agent.run(query=question, chat_history=chat_history)
            output = result["output"]
            output = output.content

        print(f"Assistant: {output}")
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=output))


if __name__ == "__main__":
    query_agent()
