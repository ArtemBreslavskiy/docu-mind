import logging
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
from indexing.loaders.base import BaseLoader
from core_schemas import Document
from src.logger.logger_setup import get_logger


class XAMLLoader(BaseLoader):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger if logger is not None else get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        raw_dir = Path(raw_dir)
        documents = []

        xaml_files = list(raw_dir.glob("*.xaml"))
        if not xaml_files:
            self.logger.warning("No XAML files found in %s", raw_dir)
            return []

        self.logger.info("Starting to load %d XAML files from %s", len(xaml_files), raw_dir)

        if show_progress_bar:
            progress_bar = tqdm(xaml_files, desc="Loading XAML", unit="file")
        else:
            progress_bar = xaml_files

        for xaml_file in progress_bar:
            content = self._read_file(xaml_file)
            if content is None:
                self.logger.warning("Could not read file: %s", xaml_file)
                continue

            soup = BeautifulSoup(content, "lxml-xml")
            root = soup.find()
            title = xaml_file.stem
            if root:
                class_name = root.get("x:Class") or root.get("x:Name")
                if class_name:
                    title = class_name
                elif root.name:
                    title = root.name

            text = soup.get_text(separator="\n", strip=True)
            if not text:
                continue

            description = f"{title}--{xaml_file.stem}--xaml"
            metadata = {
                "loaded_from": "xaml",
                "source": str(xaml_file),
                "title": title,
            }
            documents.append(Document(content=text, metadata=metadata, description=description))

        self.logger.info("Finished loading XAML files. Total documents: %d", len(documents))
        return documents

    @staticmethod
    def _read_file(file_path: Path) -> str | None:
        for encoding in ["utf-8", "utf-16", "cp1251", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
