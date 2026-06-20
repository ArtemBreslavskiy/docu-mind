from pathlib import Path
from src.config.loader import load_app_config, load_pipeline_config
from retrieval.embedders.factory import create_embedder
from indexing.chunkers.factory import create_chunker
from indexing.loaders.factory import create_loader
from retrieval.vector_stores.factory import create_vector_store
from paths.project_paths import ProjectPaths
from src.logger.logger_setup import get_logger


def index_documents():
    paths = ProjectPaths()
    app_config = load_app_config(paths.APP_CONFIG)
    pipeline_config = load_pipeline_config(paths.PIPELINE_CONFIG)

    logger = get_logger("pipeline")
    logger.info("=== Document indexing started ===")

    logger.info("Loading documents from %s", paths.RAW)
    loader = create_loader(loader_type="html", logger=logger)
    raw_docs = loader.load(raw_dir=paths.RAW, show_progress_bar=True)
    logger.info("Loaded %d documents", len(raw_docs))

    paths.TEXTS.mkdir(parents=True, exist_ok=True)
    for doc in raw_docs:
        source_name = Path(doc.metadata.get("source", "unknown")).stem
        txt_path = paths.TEXTS / f"{source_name}.txt"
        txt_path.write_text(doc.content, encoding="utf-8")
        doc.metadata["txt_path"] = str(txt_path)
    logger.info("Text copies saved to %s", paths.TEXTS)

    chunker = create_chunker(config=pipeline_config.chunker)
    chunks = chunker.split(documents=raw_docs)
    logger.info("Created %d chunks", len(chunks))

    embedder = create_embedder(config=app_config.models.embedder)
    texts = [chunk.content for chunk in chunks]
    logger.info("Generating embeddings for %d chunks...", len(texts))
    embeddings = embedder.embed(texts=texts, show_progress_bar=True)
    logger.info("Embeddings generated")

    store = create_vector_store(config=app_config.storage)
    logger.info("Saving chunks to vector store...")
    store.add(chunks, embeddings)
    logger.info("Index creation completed. Total chunks: %d", len(chunks))


if __name__ == "__main__":
    index_documents()
