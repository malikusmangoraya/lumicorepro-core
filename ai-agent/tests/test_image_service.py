"""
Tests for ImageService — real image provisioning for generated projects.
"""
import sys
import tempfile
from pathlib import Path

import pytest

from agent.image_service import ImageService, provision_images

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def empty_plan():
    return {
        "project_name": "test-site",
        "industry": "restaurant",
        "assets": {"images": []},
    }


class TestImageService:
    def test_category_mapping(self):
        svc = ImageService({"industry": "restaurant"})
        assert svc.stock_category() == "restaurant"

    def test_category_mapping_unknown_industry(self):
        svc = ImageService({"industry": "anything-unmapped"})
        assert svc.stock_category() == "business"

    def test_stock_library_has_real_files(self):
        svc = ImageService({"industry": "business"})
        images = svc.list_stock_images()
        assert len(images) > 0
        assert all(p.exists() for p in images)

    def test_all_categories_have_stock(self):
        from config.settings import ASSETS_DIR
        from agent.image_service import STOCK_CATEGORIES
        for cat in STOCK_CATEGORIES:
            d = ASSETS_DIR / "images" / cat
            pool = []
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                pool.extend(d.glob(ext))
            assert pool, f"No stock images for category '{cat}'"

    def test_provision_writes_real_files(self, empty_plan):
        with tempfile.TemporaryDirectory() as tmp:
            m = provision_images(empty_plan, Path(tmp))
            copied = m.get("copied", [])
            assert len(copied) >= 4, "Expected at least 4 real images"
            for entry in copied:
                f = Path(tmp) / entry["file"]
                assert f.exists(), f"Image not copied: {entry['file']}"
            assert "images_dir" in m

    def test_registry_entries_are_valid(self):
        from config.settings import REGISTRY_DIR, PROJECT_ROOT
        data = __import__("json").loads((REGISTRY_DIR / "images.json").read_text(encoding="utf-8"))
        assert len(data) > 30, "Registry should include the full stock library"
        local = [e for e in data if not str(e["file_path"]).startswith("http")]
        for e in local:
            assert (PROJECT_ROOT / e["file_path"]).exists(), f"Missing: {e['file_path']}"

    def test_remote_urls_flagged(self):
        svc = ImageService({})
        remote = svc.resolve_registry_item({"name": "x", "file_path": "https://images.unsplash.com/x.jpg"})
        assert remote is not None
        assert remote[0].startswith("http")