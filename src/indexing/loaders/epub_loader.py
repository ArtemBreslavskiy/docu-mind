import logging
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT
from indexing.loaders.base import BaseLoader
from core_schemas import Document
from src.logger.logger_setup import get_logger


class EPUBLoader(BaseLoader):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger or get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        raw_dir = Path(raw_dir)
        documents = []
        epub_files = list(raw_dir.glob("*.epub"))
        if not epub_files:
            self.logger.warning("No EPUB files found in %s", raw_dir)
            return []

        self.logger.info("Starting to load %d EPUB files from %s", len(epub_files), raw_dir)
        progress_bar = tqdm(epub_files, desc="Loading EPUB", unit="file") if show_progress_bar else epub_files

        for epub_file in progress_bar:
            try:
                book = epub.read_epub(epub_file)
                title = book.get_metadata('DC', 'title')
                title = title[0][0] if title else epub_file.stem
                full_text = []
                for item in book.get_items_of_type(ITEM_DOCUMENT):
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    full_text.append(soup.get_text(separator='\n'))
                text = '\n'.join(full_text)
                if not text.strip():
                    continue

                meta = {
                    "loaded_from": "epub",
                    "source": str(epub_file),
                    "title": title,
                    "author": ", ".join([auth[0] for auth in book.get_metadata('DC', 'creator')]) if book.get_metadata('DC', 'creator') else "",
                }
                description = f"{title}--{meta.get('author', '')}"

                documents.append(Document(
                    content=text,
                    metadata=meta,
                    description=description
                ))
            except Exception as e:
                self.logger.error("Failed to process %s: %s", epub_file, e)

        self.logger.info("Finished loading EPUB files. Total documents: %d", len(documents))
        return documents
