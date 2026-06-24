import logging
import uuid
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from trafilatura import extract
from loaders.base import BaseLoader
from core_schemas import Document
from src.logger.logger_setup import get_logger


class HTMLLoader(BaseLoader):
    def __init__(self, logger: logging.Logger = None, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger if logger is not None else get_logger("pipeline")
        if logger is None:
            self.logger.disabled = True

    def load(self, raw_dir: str | Path, show_progress_bar: bool = True) -> list[Document]:
        raw_dir = Path(raw_dir)
        documents = []

        if not raw_dir.exists():
            msg = "Directory does not exist: %s", raw_dir
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        html_files = list(raw_dir.glob("*.html"))
        if not html_files:
            self.logger.warning("No HTML files found in %s", raw_dir)
            return []

        self.logger.info("Starting to load %d HTML files from %s", len(html_files), raw_dir)

        if show_progress_bar:
            progress_bar = tqdm(html_files, desc="Loading HTML", unit="file")
        else:
            progress_bar = html_files

        for html_file in progress_bar:
            content = self._read_file(html_file)
            if content is None:
                self.logger.warning("Could not read file: %s", html_file)
                continue

            soup = BeautifulSoup(content, "lxml")
            page_title = soup.title.string.strip() if soup.title and soup.title.string else html_file.stem
            meta_tags = self._get_meta_tags(soup)
            sections = self._split_by_sections(soup)

            if not sections:
                text = extract(content, include_comments=False, include_tables=False)
                if text:
                    description = f"{page_title}--{str(uuid.uuid4())[:8]}"
                    metadata = {
                        "loaded_from": "html",
                        "source": str(html_file),
                        "title": page_title,
                    }
                    metadata.update(meta_tags)
                    documents.append(Document(content=text, metadata=metadata, description=description))
                continue

            self.logger.debug("Found %d sections in %s", len(sections), html_file.name)
            for section_title, section_text in sections:
                if not section_text:
                    continue
                description = f"{page_title}--{section_title}--{str(uuid.uuid4())[:8]}"
                metadata = {
                    "loaded_from": "html",
                    "source": str(html_file),
                    "title": page_title,
                    "section": section_title,
                }
                metadata.update(meta_tags)
                documents.append(Document(content=section_text, metadata=metadata, description=description))

        self.logger.info("Finished loading. Total documents: %d", len(documents))
        return documents

    @staticmethod
    def _read_file(file_path: Path) -> str | None:
        for encoding in ["utf-8", "cp1251", "latin-1", "iso-8859-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None

    @staticmethod
    def _get_meta_tags(soup: BeautifulSoup) -> dict:
        meta = {}
        type_tag = soup.find("meta", attrs={"name": "type"})
        if type_tag and type_tag.get("content"):
            meta["content_type"] = type_tag["content"]

        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
        if keywords_tag and keywords_tag.get("content"):
            meta["keywords"] = keywords_tag["content"]

        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta["description"] = desc_tag["content"]

        author_tag = soup.find("meta", attrs={"name": "author"})
        if author_tag and author_tag.get("content"):
            meta["author"] = author_tag["content"]

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            meta["opengraph_title"] = og_title["content"]

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            meta["opengraph_description"] = og_desc["content"]

        date_tag = soup.find("meta", attrs={"name": "date"})
        if not date_tag:
            date_tag = soup.find("meta", property="article:published_time")
        if date_tag and date_tag.get("content"):
            meta["publication_date"] = date_tag["content"]

        return meta

    @staticmethod
    def _split_by_sections(soup: BeautifulSoup) -> list[tuple[str, str]]:
        sections = []
        current_title = "Introduction"
        current_text = []

        for tag in soup.find_all(["h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "div"]):
            if tag.name in ["h2", "h3", "h4", "h5", "h6"]:
                if current_text:
                    sections.append((current_title, "\n".join(current_text)))
                current_title = tag.get_text(strip=True)
                current_text = []

            else:
                text = tag.get_text(strip=True)
                if text:
                    current_text.append(text)

        if current_text:
            sections.append((current_title, "\n".join(current_text)))
        return sections
