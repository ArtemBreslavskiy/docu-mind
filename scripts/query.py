from src.config.loader import load_app_config, load_pipeline_config
from src.core.embedder.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.storage.vector_store.store_factory import create_vector_store
from src.core.retriever.retriever_factory import create_retriever
from src.core.models.models_factory import create_model
from paths.project_paths import ProjectPaths


def query():
    paths = ProjectPaths()
    app_config = load_app_config(path=paths.APP_CONFIG)
    pipeline_config = load_pipeline_config(path=paths.PIPELINE_CONFIG)

    embedder = SentenceTransformerEmbedder(config=app_config.models.embedding)
    store = create_vector_store(config=app_config.data.storage)
    retriever = create_retriever(config=pipeline_config.retriever, embedder=embedder, store=store)
    model = create_model(config=app_config.models.llm.model)

    while True:
        question = input("\nEnter a question (or 'exit' to exit): ")
        if question.lower() == "exit":
            break

        results = retriever.retrieve(query=question, k=5)
        chunks = [res.chunk for res in results]

        answer = model.generate(question=question, context_chunks=chunks)

        print("\nAnswer:\n", answer)
        print("\nSources:")
        for i, chunk in enumerate(chunks, 1):
            print(f"[{i}] {chunk.metadata.get("source", "?")}")


if __name__ == "__main__":
    query()
