from src.config.loader import load_app_config, load_pipeline_config
from src.core.embedder.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.data.chunkers.chunker_factory import create_chunker
from src.data.loaders.loader_factory import create_loader
from src.storage.vector_store.store_factory import create_vector_store
from paths.project_paths import ProjectPaths


def main():
    paths = ProjectPaths()
    app_config = load_app_config(paths.APP_CONFIG)
    pipeline_config = load_pipeline_config(paths.PIPELINE_CONFIG)

    loader = create_loader(app_config.data.loader)
    raw_docs = loader.load(paths.RAW)

    chunker = create_chunker(pipeline_config.chunker)
    chunks = chunker.split(raw_docs)

    embedder = SentenceTransformerEmbedder(app_config.models.embedding)
    texts = [chunk.content for chunk in chunks]
    embeddings = embedder.embed(texts)

    store = create_vector_store(app_config.data.storage)
    store.add(chunks, embeddings)

    print(f"✅ Index created: {len(chunks)} chunks")


if __name__ == "__main__":
    main()
