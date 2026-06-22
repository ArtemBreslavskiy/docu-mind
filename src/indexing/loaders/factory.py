from src.indexing.loaders.base import BaseLoader


def create_loader(loader_type: str) -> BaseLoader:
    if loader_type == "html":
        from .html_loader import HTMLLoader
        return HTMLLoader()

    elif loader_type == "pdf":
        from .pdf_loader import PDFLoader
        return PDFLoader()

    elif loader_type == "docx":
        from .docx_loader import DocxLoader
        return DocxLoader()

    elif loader_type == "markdown":
        from .markdown_loader import MarkdownLoader
        return MarkdownLoader()

    elif loader_type == "epub":
        from .epub_loader import EPUBLoader
        return EPUBLoader()

    elif loader_type == "text":
        from .text_loader import TextLoader
        return TextLoader()

    elif loader_type == "xaml":
        from .xaml_loader import XAMLLoader
        return XAMLLoader()

    else:
        raise ValueError(f"Unknown loader type: {loader_type}")
