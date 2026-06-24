import asyncio
from dotenv import load_dotenv
from src.configs.loader import load_pipeline_config
from embedders.factory import create_embedder
from document_processors.factory import create_document_processor
from vector_stores.factory import create_vector_store
from paths.project_paths import ProjectPaths
from src.logger.logger_setup import get_logger


async def index_documents():
    paths = ProjectPaths()
    pipeline_config = load_pipeline_config(paths.PIPELINE_CONFIG)
    load_dotenv()

    logger = get_logger("pipeline")
    logger.info("=== Document documents started ===")

    document_processor = create_document_processor(pipeline_config.document_processor)
    chunks = await document_processor.process(paths.RAW, show_progress_bar=True)

    embedder = create_embedder(config=pipeline_config.retriever.embedder)
    texts = [chunk.content for chunk in chunks]
    logger.info("Generating embeddings for %d chunks...", len(texts))
    embeddings = embedder.embed(texts=texts, show_progress_bar=True)
    logger.info("Embeddings generated")

    store = create_vector_store(config=pipeline_config.retriever.vector_storage)
    logger.info("Saving chunks to vector store...")
    store.add(chunks, embeddings)
    logger.info("Index creation completed. Total chunks: %d", len(chunks))


if __name__ == "__main__":
    asyncio.run(index_documents())
