from pathlib import Path
from typing import Union
from langchain_community.document_loaders import BSHTMLLoader
from src.data.loaders.base import BaseLoader
from src.core.schemas import Document


class HTMLLoader(BaseLoader):
    def load(self, raw_dir: Union[str, Path]) -> list[Document]:
        documents = []
        raw_dir = Path(raw_dir)

        if not raw_dir.exists():
            raise FileNotFoundError(f"The {raw_dir} directory does not exist")

        for html_file in raw_dir.glob("*.html"):
            loader = BSHTMLLoader(str(html_file))
            langchain_docs = loader.load()

            for lc_doc in langchain_docs:
                documents.append(Document(page_content=lc_doc.page_content, metadata=lc_doc.metadata or {}))

        return documents
