import logging
from pathlib import Path
from tqdm import tqdm
from loaders.base import BaseLoader
from core_schemas import Document
from src.logger.logger_setup import get_logger


class MarkdownLoader(BaseLoader):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger or get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        raw_dir = Path(raw_dir)
        documents = []
        md_files = list(raw_dir.glob("*.md"))
        if not md_files:
            self.logger.warning("No Markdown files found in %s", raw_dir)
            return []

        self.logger.info("Starting to load %d Markdown files from %s", len(md_files), raw_dir)
        progress_bar = tqdm(md_files, desc="Loading MD", unit="file") if show_progress_bar else md_files

        for md_file in progress_bar:
            try:
                content = md_file.read_text(encoding="utf-8")
                if not content.strip():
                    continue
                title = md_file.stem
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                meta = {
                    "loaded_from": "markdown",
                    "source": str(md_file),
                    "title": title,
                }
                description = f"{title}--{md_file.name}"

                documents.append(Document(
                    content=content,
                    metadata=meta,
                    description=description
                ))
            except Exception as e:
                self.logger.error("Failed to process %s: %s", md_file, e)

        self.logger.info("Finished loading Markdown files. Total documents: %d", len(documents))
        return documents
