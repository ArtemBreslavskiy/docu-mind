from pathlib import Path
from trafilatura import extract
from src.data.loaders.base import BaseLoader
from src.core.schemas import Document


class HTMLLoader(BaseLoader):
    def load(self, raw_dir: str | Path) -> list[Document]:
        raw_dir = Path(raw_dir)
        documents = []

        if not raw_dir.exists():
            raise FileNotFoundError(f"The {raw_dir} directory does not exist")

        for html_file in raw_dir.glob("*.html"):
            content = self._read_file(html_file)
            if content is None:
                continue

            text = extract(content, include_comments=False, include_tables=False)
            if text:
                documents.append(Document(
                    page_content=text,
                    metadata={"source": str(html_file)}
                ))

        return documents

    @staticmethod
    def _read_file(file_path: Path) -> str | None:
        for encoding in ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
