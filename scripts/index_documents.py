import asyncio
from dotenv import load_dotenv
from src.configs.loader import load_pipeline_config
from data.vectors_builders.factory import create_vectors_builder
from data.graph_builders.factory import create_graph_builder
from data.document_processors.factory import create_document_processor
from utils.logger_setup import get_logger
from paths.project_paths import ProjectPaths


async def index_documents():
    paths = ProjectPaths()
    pipeline_config = load_pipeline_config(paths.PIPELINE_CONFIG)
    load_dotenv()

    logger = get_logger("pipeline")

    chunks = None
    document_processor = create_document_processor(config=pipeline_config.document_processor, logger=logger)
    if document_processor:
        chunks = await document_processor.process(paths.RAW, show_progress_bar=True)

    graph_builder = create_graph_builder(config=pipeline_config.graph_builder, logger=logger)
    if graph_builder and chunks:
        graph_builder.build(chunks=chunks, show_progress_bar=True)

    vectors_builder = create_vectors_builder(config=pipeline_config.vectors_builder, logger=logger)
    if vectors_builder and chunks:
        vectors_builder.build(chunks=chunks, show_progress_bar=True)


if __name__ == "__main__":
    asyncio.run(index_documents())
