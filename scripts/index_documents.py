from pathlib import Path
from src.config.loader import load_app_config, load_pipeline_config
from src.core.embedder.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.data.chunkers.chunker_factory import create_chunker
from src.data.loaders.loader_factory import create_loader
from src.storage.vector_store.store_factory import create_vector_store
from paths.project_paths import ProjectPaths


def index_documents():
    paths = ProjectPaths()
    app_config = load_app_config(paths.APP_CONFIG)
    pipeline_config = load_pipeline_config(paths.PIPELINE_CONFIG)

    loader = create_loader(config=app_config.data.loader)
    raw_docs = loader.load(raw_dir=paths.RAW)

    paths.TEXTS.mkdir(parents=True, exist_ok=True)
    for doc in raw_docs:
        source_name = Path(doc.metadata.get("source", "unknown")).stem
        txt_path = paths.TEXTS / f"{source_name}.txt"
        txt_path.write_text(doc.page_content, encoding="utf-8")
        doc.metadata["txt_path"] = str(txt_path)

    chunker = create_chunker(config=pipeline_config.chunker)
    chunks = chunker.split(documents=raw_docs)

    embedder = SentenceTransformerEmbedder(config=app_config.models.embedding)
    texts = [chunk.content for chunk in chunks]
    embeddings = embedder.embed(texts=texts)

    store = create_vector_store(config=app_config.data.storage)
    store.add(chunks, embeddings)

    print(f"✅ Index created: {len(chunks)} chunks")


if __name__ == "__main__":
    index_documents()
