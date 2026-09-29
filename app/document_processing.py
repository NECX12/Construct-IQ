from pathlib import Path


def read_text_file(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".csv", ".md"}:
        return content.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported text format: {suffix or 'unknown'}")


def pdf_page_count(content: bytes) -> int:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Install PyMuPDF to process PDF files") from exc
    document = fitz.open(stream=content, filetype="pdf")
    return document.page_count
