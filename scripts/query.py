from src.config.loader import load_app_config, load_pipeline_config
from src.core.embedder.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.storage.vector_store.store_factory import create_vector_store
from src.core.retriever.retriever_factory import create_retriever
from src.core.generator.generator_factory import create_generator
from paths.project_paths import ProjectPaths


def query():
    paths = ProjectPaths()
    app_config = load_app_config(paths.APP_CONFIG)
    pipeline_config = load_pipeline_config(paths.PIPELINE_CONFIG)

    embedder = SentenceTransformerEmbedder(app_config.models.embedding)
    store = create_vector_store(app_config.data.storage)
    retriever = create_retriever(pipeline_config.retriever, embedder, store)
    generator = create_generator(app_config.models.llm)

    while True:
        question = input("\nEnter a question (or 'exit' to exit): ")
        if question.lower() == "exit":
            break

        results = retriever.retrieve(question, 5)
        chunks = [res.chunk for res in results]

        answer = generator.generate(question, chunks)

        print("\nAnswer:\n", answer)
        print("\nSources:")
        for i, chunk in enumerate(chunks, 1):
            print(f"[{i}] {chunk.metadata.get("source", "?")}")


if __name__ == "__main__":
    query()
