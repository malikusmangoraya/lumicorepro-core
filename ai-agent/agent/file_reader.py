"""
FileReader — safe text extraction from user-uploaded documents.

Supported:
  - Plain text / code (txt, js, py, json, css, html, md, csv, ...)
  - PDFs (pypdf/pdfminer if installed — graceful fallback)
  - Word .docx (python-docx if installed)
  - Spreadsheets .xlsx/.csv (openpyxl if installed)
  - Archives .zip (lists file structure)

Every extractor degrades gracefully — a missing library never raises.
"""
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import agent_logger

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".xml", ".yaml", ".yml",
    ".js", ".jsx", ".ts", ".tsx", ".py", ".css", ".scss", ".html", ".htm",
    ".sql", ".sh", ".env", ".ini", ".cfg", ".conf", ".log",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".bmp"}

MAX_TEXT_CHARS = 12_000  # keep prompt size sane


def _read_pdf(data: bytes) -> str:
    text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(__import__("io").BytesIO(data))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    except ImportError:
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
            import io, tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
                fh.write(data)
                fh.flush()
                tmp = fh.name
            try:
                text = pdfminer_extract(tmp)
            finally:
                os.unlink(tmp)
        except Exception:
            text = "[PDF: could not be parsed without pypdf/pdfminer — text not readable]"
    except Exception as exc:
        agent_logger.warning(f"FileReader PDF parse failed: {exc}")
        text = f"[PDF parse failed: {exc}]"
    return text


def _read_docx(data: bytes) -> str:
    try:
        import io
        import docx  # python-docx
        document = docx.Document(io.BytesIO(data))
        paragraphs = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(paragraphs)
    except Exception as exc:
        agent_logger.warning(f"FileReader docx parse failed (install python-docx): {exc}")
        return f"[DOCX: text could not be extracted — {exc}]"


def _read_xlsx(data: bytes) -> str:
    try:
        import io
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        parts = []
        for sheet in wb.worksheets[:5]:
            rows = []
            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if i >= 200:
                    break
                rows.append(" | ".join("" if c is None else str(c) for c in row))
            parts.append(f"[Sheet: {sheet.title}]" + "\n" + "\n".join(rows))
        wb.close()
        return "\n\n".join(parts)
    except Exception as exc:
        agent_logger.warning(f"FileReader xlsx parse failed (install openpyxl): {exc}")
        return f"[XLSX: could not be read — {exc}]"


def _read_zip(data: bytes) -> str:
    try:
        import io
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()[:100]
            return "Archive contents:\n" + "\n".join(" - " + n for n in names)
    except Exception as exc:
        return f"[ZIP: could not list contents — {exc}]"


def read_file_content(filename: str, data: bytes) -> Optional[str]:
    """Return plain-text content for a document. Returns None for images."""
    name = (filename or "").lower()
    ext = Path(name).suffix
    if ext in (".pdf",):
        return _read_pdf(data)
    if ext in (".docx",):
        return _read_docx(data)
    if ext in (".xlsx", ".xlsm"):
        return _read_xlsx(data)
    if ext == ".zip":
        return _read_zip(data)
    if ext in TEXT_EXTENSIONS or ext == "":
        try:
            return data.decode("utf-8", errors="replace")[:MAX_TEXT_CHARS]
        except Exception:
            return None
    agent_logger.info(f"FileReader: no extractor for '{filename}' — skipped")
    return None


def describe_attachments(files: List[Dict]) -> str:
    """Build a compact context block describing all attached files for the LLM."""
    if not files:
        return ""
    lines: List[str] = ["[Attached files by the user:]"]
    for f in files[:25]:
        fname = f.get("filename", "file")
        ftype = (f.get("type") or "").lower()
        ext = Path(fname).suffix.lower()
        kind = "image" if (ftype.startswith("image/") or ext in IMAGE_EXTENSIONS) else "document"
        lines.append(f" - {fname} ({kind})")
        if kind == "document" and f.get("content"):
            snippet = f["content"][:1500].replace("\n", " ")
            lines.append(f"    > {snippet}")
            if len(f["content"]) > 1500:
                lines[-1] += " …"
    return "\n".join(lines)


def extract_files(files: List[Dict]) -> Dict[str, List[Dict]]:
    """Decode base64 uploads into categorized metadata + text content.

    Returns {"images": [...], "documents": [...]}. Each entry carries:
      filename, type, mime, content (documents only), data_uri (images only)
    """
    result: Dict[str, List[Dict]] = {"images": [], "documents": []}
    for f in files or []:
        filename = (f.get("filename") or "file").strip()
        mime = (f.get("type") or "").lower()
        data_uri = (f.get("data") or "").strip()
        if not data_uri:
            continue
        try:
            header, _, b64 = data_uri.partition(",")
            import base64
            raw = base64.b64decode(b64)
        except Exception:
            continue
        ext = Path(filename).suffix.lower()
        is_image = mime.startswith("image/") or ext in IMAGE_EXTENSIONS
        entry = {"filename": filename, "type": mime, "ext": ext}
        if is_image:
            entry["data"] = data_uri
            result["images"].append(entry)
        else:
            entry["content"] = read_file_content(filename, raw) or ""
            result["documents"].append(entry)
    return result