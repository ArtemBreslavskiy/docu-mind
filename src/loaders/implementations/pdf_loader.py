import logging
from pathlib import Path
from tqdm import tqdm
import fitz
from loaders.base import BaseLoader
from core_schemas import Document
from src.logger.logger_setup import get_logger


class PDFLoader(BaseLoader):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger or get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        raw_dir = Path(raw_dir)
        documents = []
        pdf_files = list(raw_dir.glob("*.pdf"))
        if not pdf_files:
            self.logger.warning("No PDF files found in %s", raw_dir)
            return []

        self.logger.info("Starting to load %d PDF files from %s", len(pdf_files), raw_dir)
        progress_bar = tqdm(pdf_files, desc="Loading PDF", unit="file") if show_progress_bar else pdf_files

        for pdf_file in progress_bar:
            try:
                doc = fitz.open(pdf_file)
                text = "\n".join(page.get_text() for page in doc)
                if not text.strip():
                    self.logger.debug("No text extracted from %s", pdf_file)
                    continue

                pdf_metadata = doc.metadata
                meta = {
                    "loaded_from": "pdf",
                    "source": str(pdf_file),
                    "title": pdf_metadata.get("title", pdf_file.stem),
                    "author": pdf_metadata.get("author", ""),
                    "creation_date": pdf_metadata.get("creationDate", ""),
                    "num_pages": len(doc)
                }
                meta = {k: v for k, v in meta.items() if v}
                description = f"{meta.get('title', pdf_file.stem)}--{len(doc)}p"

                documents.append(Document(
                    content=text,
                    metadata=meta,
                    description=description
                ))
                doc.close()
            except Exception as e:
                self.logger.error("Failed to process %s: %s", pdf_file, e)

        self.logger.info("Finished loading PDF files. Total documents: %d", len(documents))
        return documents
