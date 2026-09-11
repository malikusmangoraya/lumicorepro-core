"""
Tests for FileReader — safe document text extraction + attachment context.
"""
import base64
import sys
from pathlib import Path

from agent.file_reader import (
    describe_attachments,
    extract_files,
    read_file_content,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _b64(text: str) -> str:
    return "data:text/plain;base64," + base64.b64encode(text.encode("utf-8")).decode("ascii")


class TestFileReader:
    def test_reads_plain_text(self):
        assert "hello world" in read_file_content("note.txt", b"hello world")

    def test_reads_code_file(self):
        content = read_file_content("App.jsx", b"export default function App() {}")
        assert "export default function App" in content

    def test_pdf_degrades_gracefully(self):
        content = read_file_content("report.pdf", b"%PDF-fake")
        assert content is not None

    def test_unknown_extension_returns_none(self):
        assert read_file_content("movie.mp4", b"data") is None

    def test_extract_files_categorizes_images_and_docs(self):
        files = [
            {"filename": "shot.png", "type": "image/png", "data": "data:image/png;base64,AAECAw=="},
            {"filename": "brief.txt", "type": "text/plain", "data": _b64("Build a bakery site")},
        ]
        result = extract_files(files)
        assert len(result["images"]) == 1
        assert len(result["documents"]) == 1
        assert result["documents"][0]["content"] == "Build a bakery site"

    def test_extract_files_categorizes_by_extension(self):
        files = [{"filename": "design.png", "type": "", "data": "data:image/png;base64,AAECAw=="}]
        result = extract_files(files)
        assert len(result["images"]) == 1

    def test_describe_attachments_renders_context_block(self):
        docs = [{"filename": "brief.txt", "type": "text/plain", "content": "Bakery, pastel palette"}]
        block = describe_attachments(docs)
        assert "brief.txt" in block
        assert "Bakery" in block

    def test_extract_files_skips_invalid_base64(self):
        files = [{"filename": "bad.txt", "type": "text/plain", "data": "data:text/plain;base64,!!!notbase64"}]
        result = extract_files(files)
        assert len(result["documents"]) == 0

    def test_describe_attachments_empty(self):
        assert describe_attachments([]) == ""