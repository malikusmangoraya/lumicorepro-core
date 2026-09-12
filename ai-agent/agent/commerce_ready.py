"""
LUMICORE_COMMERCE_READY
Deterministic, idempotent post-scaffold injection that turns every generated
storefront into a production-ready earning store (backend + shop + checkout +
admin). No AI, no network, no native deps — safe to run on every generation.
"""
import os
import json
import shutil
import logging

agent_logger = logging.getLogger("LumicoreAgent")

API_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "backend-library",
    "commerce-live-backend",
)

DEFAULT_CATALOG = [
    {"id": "p1", "title": "Signature Product One", "tagline": "Best seller", "price": 1499},
    {"id": "p2", "title": "Growth Product Two", "tagline": "Customer favourite", "price": 2499},
    {"id": "p3", "title": "Premium Product Three", "tagline": "Premium pick", "price": 4499},
    {"id": "p4", "title": "Starter Bundle", "tagline": "Economy pack", "price": 999},
    {"id": "p5", "title": "Family Offer", "tagline": "Worth every rupee", "price": 3499},
    {"id": "p6", "title": "Gift Card — Rs. 2000", "tagline": "Digital, instant", "price": 2000},
    {"id": "p7", "title": "Gift Card — Rs. 5000", "tagline": "Digital, instant", "price": 5000},
    {"id": "p8", "title": "Exclusive Limited Pack", "tagline": "While stocks last", "price": 5999},
]

STORE_PAGE = "Store"
CART_PAGE = "Cart"


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _copy(src: str, dst: str) -> bool:
    if os.path.isfile(src) and not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        return True
    return False


def inject_commerce(project_dir: str, spec: dict) -> dict:
    """Add the live-commerce stack to a generated project. Idempotent."""
    layout = str(spec.get("layout_mode", ""))
    if "static" not in layout.lower():
        return {"applies": False, "note": "transactional layout — commerce scaffold already expected"}

    base = project_dir
    frontend = os.path.join(base, "frontend")
    fe_src = os.path.join(frontend, "src")
    backend = os.path.join(base, "backend")

    made: list[str] = []

    # 1. Live order backend (only when the project has none).
    if os.path.isdir(frontend) and not os.path.exists(os.path.join(backend, "server.js")):
        os.makedirs(backend, exist_ok=True)
        for fname in ("server.js", "package.json", ".env.example"):
            _copy(os.path.join(API_SRC, fname), os.path.join(backend, fname))
        _write(os.path.join(backend, "data", "orders.json"), "[]")
        _copy(os.path.join(API_SRC, "render.yaml"), os.path.join(backend, "render.yaml"))
        _copy(os.path.join(API_SRC, "Procfile"), os.path.join(backend, "Procfile"))
        _copy(os.path.join(API_SRC, "admin.html"), os.path.join(frontend, "public", "admin.html"))
        made += ["backend/server.js", "backend/data/orders.json", "frontend/public/admin.html"]

    # 2. Real product catalog (editable single source).
    catalog_path = os.path.join(fe_src, "data", "catalog.json")
    if not os.path.exists(catalog_path):
        _write(catalog_path, json.dumps(DEFAULT_CATALOG, indent=2, ensure_ascii=False))
        made.append("frontend/src/data/catalog.json")

    # 3. Shop + Cart pages.
    pages = os.path.join(fe_src, "pages")
    for page in (STORE_PAGE, CART_PAGE):
        src_page = os.path.join(API_SRC, "frontend-pages", f"{page}.jsx")
        dst_page = os.path.join(pages, f"{page}.jsx")
        if not os.path.exists(dst_page):
            _copy(src_page, dst_page)
            made.append(f"frontend/src/pages/{page}.jsx")

    # 4. Wire Store.jsx (mockApi) to the catalog when mockApi exists.
    mock = os.path.join(fe_src, "services", "mockApi.js")
    if os.path.isfile(mock):
        content = open(mock, encoding="utf-8").read()
        if "catalog.json" not in content:
            content = content.replace(
                os.path.join("..", "data", "catalog.json"),
                os.path.join("..", "data", "catalog.json"),
            )
            if "import catalogData from" not in content:
                content = content.replace(
                    "const delay = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms));",
                    "import catalogData from '../data/catalog.json';\n\n"
                    "const delay = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms));",
                )
            import re
            content = re.sub(r"products: \[.*?\],", "products: catalogData,", content, flags=re.S)
            _write(mock, content)
            made.append("frontend/src/services/mockApi.js")

    # 5. Routes + lazy imports (defensive — only when the canonical pattern exists).
    app_path = os.path.join(fe_src, "App.jsx")
    if os.path.isfile(app_path):
        content = open(app_path, encoding="utf-8").read()
        if "pages/Store" not in content:
            before = content.count("Route path=")
            content = content.replace(
                "const Contact = lazy(() => import('./pages/Contact'));",
                "const Contact = lazy(() => import('./pages/Contact'));\n"
                f"const {STORE_PAGE} = lazy(() => import('./pages/{STORE_PAGE}'));\n"
                f"const {CART_PAGE} = lazy(() => import('./pages/{CART_PAGE}'));",
            )
            content = content.replace(
                '<Route path="/contact" element={<Contact />} />',
                '<Route path="/contact" element={<Contact />} />\n'
                '<Route path="/shop" element={<' + STORE_PAGE + ' />} />\n'
                '<Route path="/cart" element={<' + CART_PAGE + ' />} />',
            )
            if content.count("Route path=") > before:
                _write(app_path, content)
                made.append("frontend/src/App.jsx")

    if made:
        agent_logger.info(f"[COMMERCE_READY] injected: {made}")
    return {"applies": True, "injected": made}