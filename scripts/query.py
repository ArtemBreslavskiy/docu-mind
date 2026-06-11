from src.config.loader import load_app_config, load_pipeline_config
from src.core.embedder.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.storage.vector_store.store_factory import create_vector_store
from src.core.retriever.retriever_factory import create_retriever
from paths.project_paths import ProjectPaths


def query():
    paths = ProjectPaths()
    app_config = load_app_config(paths.APP_CONFIG)
    pipeline_config = load_pipeline_config(paths.PIPELINE_CONFIG)

    embedder = SentenceTransformerEmbedder(app_config.models.embedding)
    store = create_vector_store(app_config.data.storage)
    retriever = create_retriever(pipeline_config.retriever, embedder, store)

    question = input("Enter a question: ")
    results = retriever.retrieve(question, k=5)

    for i, res in enumerate(results, 1):
        print(f"\n--- Result {i} (score: {res.score:.3f}) ---")
        print(res.chunk.content[:500])


if __name__ == "__main__":
    query()
