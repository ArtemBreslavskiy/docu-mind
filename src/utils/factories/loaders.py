from data.loaders.base import BaseLoader


def create_loader(loader_type: str) -> BaseLoader:
    if loader_type == "html":
        from data.loaders.implementations.html_loader import HTMLLoader
        return HTMLLoader()

    elif loader_type == "pdf":
        from data.loaders.implementations.pdf_loader import PDFLoader
        return PDFLoader()

    elif loader_type == "docx":
        from data.loaders.implementations.docx_loader import DocxLoader
        return DocxLoader()

    elif loader_type == "markdown":
        from data.loaders.implementations.markdown_loader import MarkdownLoader
        return MarkdownLoader()

    elif loader_type == "epub":
        from data.loaders.implementations.epub_loader import EPUBLoader
        return EPUBLoader()

    elif loader_type == "text":
        from data.loaders.implementations.text_loader import TextLoader
        return TextLoader()

    elif loader_type == "xaml":
        from data.loaders.implementations.xaml_loader import XAMLLoader
        return XAMLLoader()

    else:
        raise ValueError(f"Unknown loader type: {loader_type}")
