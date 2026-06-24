from loaders.base import BaseLoader


def create_loader(loader_type: str) -> BaseLoader:
    if loader_type == "html":
        from loaders.implementations.html_loader import HTMLLoader
        return HTMLLoader()

    elif loader_type == "pdf":
        from loaders.implementations.pdf_loader import PDFLoader
        return PDFLoader()

    elif loader_type == "docx":
        from loaders.implementations.docx_loader import DocxLoader
        return DocxLoader()

    elif loader_type == "markdown":
        from loaders.implementations.markdown_loader import MarkdownLoader
        return MarkdownLoader()

    elif loader_type == "epub":
        from loaders.implementations.epub_loader import EPUBLoader
        return EPUBLoader()

    elif loader_type == "text":
        from loaders.implementations.text_loader import TextLoader
        return TextLoader()

    elif loader_type == "xaml":
        from loaders.implementations.xaml_loader import XAMLLoader
        return XAMLLoader()

    else:
        raise ValueError(f"Unknown loader type: {loader_type}")
