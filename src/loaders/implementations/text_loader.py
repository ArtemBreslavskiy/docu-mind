import logging
from pathlib import Path
from tqdm import tqdm
from loaders.base import BaseLoader
from core_schemas import Document
from src.logger.logger_setup import get_logger


class TextLoader(BaseLoader):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger or get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        raw_dir = Path(raw_dir)
        documents = []
        text_files = list(raw_dir.glob("*.txt")) + list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.json"))
        if not text_files:
            self.logger.warning("No text files found in %s", raw_dir)
            return []

        self.logger.info("Starting to load %d text files from %s", len(text_files), raw_dir)
        progress_bar = tqdm(text_files, desc="Loading Text", unit="file") if show_progress_bar else text_files

        for text_file in progress_bar:
            try:
                content = text_file.read_text(encoding="utf-8")
                if not content.strip():
                    continue
                meta = {
                    "loaded_from": "text",
                    "source": str(text_file),
                    "title": text_file.stem,
                    "extension": text_file.suffix,
                }
                description = f"{text_file.stem}--text"

                documents.append(Document(
                    content=content,
                    metadata=meta,
                    description=description
                ))
            except Exception as e:
                self.logger.error("Failed to process %s: %s", text_file, e)

        self.logger.info("Finished loading text files. Total documents: %d", len(documents))
        return documents
