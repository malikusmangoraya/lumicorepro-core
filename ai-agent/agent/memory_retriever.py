import sqlite3
import threading
import time
from typing import Dict, Any, List, Optional
from config.settings import AGENT_DB_PATH
from utils.logger import agent_logger
from utils.semantic import semantic_similarity, tokenize, overlap_ratio

# Thread-local storage for DB connections
_thread_local = threading.local()

# Catalog tables that carry adaptive usage counters (reverse map for bump_usage).
USAGE_TABLES = {
    "template": "templates_index",
    "component": "components_index",
    "asset": "assets_index",
    "backend": "backend_index",
}
USAGE_CAP = 50

class MemoryRetriever:
    """Local-First Memory Retriever with thread-safe connections, WAL journal mode, and busy lock retries."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(AGENT_DB_PATH)

    def _usage_bias(self, item: Dict[str, Any]) -> int:
        """Adaptive bias: components/templates proven across prior projects rank higher."""
        try:
            return min(int(item.get("usage_count") or 0), USAGE_CAP)
        except (TypeError, ValueError):
            return 0

    def bump_usage(self, kind: str, name: str) -> None:
        """Increment the adaptive usage counter for a selected catalog entry."""
        table = USAGE_TABLES.get(kind)
        if not table or not name:
            return
        try:
            self._execute_write_retry(
                f"UPDATE {table} SET usage_count = COALESCE(usage_count, 0) + 1 WHERE name = ?",
                (name,),
            )
        except Exception as exc:  # pragma: no cover
            agent_logger.warning(f"bump_usage failed for {kind} '{name}': {exc}")

    def memory_insights(self, limit: int = 20) -> Dict[str, Any]:
        """Adaptive memory snapshot: usage leaderboards per catalog plus search volume."""
        try:
            conn = self._get_connection()
            insights: Dict[str, Any] = {}
            for kind, table in USAGE_TABLES.items():
                rows = conn.execute(
                    f"SELECT name, category, usage_count FROM {table} "
                    "ORDER BY COALESCE(usage_count, 0) DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                insights[kind] = [dict(r) for r in rows]
            insights["search_history_count"] = conn.execute(
                "SELECT COUNT(*) FROM search_history"
            ).fetchone()[0]
            return insights
        except Exception as exc:
            agent_logger.error(f"Error reading memory insights: {exc}")
            return {}

    def recent_searches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Most recent search-history entries for observability."""
        try:
            conn = self._get_connection()
            rows = conn.execute(
                "SELECT * FROM search_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            agent_logger.error(f"Error reading search history: {exc}")
            return []

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local SQLite connection with WAL mode and busy timeout configured."""
        if not hasattr(_thread_local, "connection") or _thread_local.connection is None:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            _thread_local.connection = conn
        return _thread_local.connection

    def _execute_write_retry(self, query: str, params: tuple = ()) -> None:
        """Execute write query with max 3 retries on SQLite lock operational errors."""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < max_retries:
                    agent_logger.warning(f"SQLite DB locked (attempt {attempt}/{max_retries}). Retrying write...")
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    agent_logger.error(f"SQLite operational write error: {e}")
                    raise e

    def search_templates(self, category: str, industry: str, features: List[str]) -> List[Dict[str, Any]]:
        """Search and score templates matching category, industry, and features with synonym expansion."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM templates_index")
            rows = cursor.fetchall()

            # Industry & Category Synonym Map
            synonyms = {
                "business": ["corporate", "agency", "company", "business"],
                "realestate": ["property", "house", "listings", "realestate"],
                "restaurant": ["cafe", "food", "dining", "restaurant"],
                "portfolio": ["personal", "brand", "resume", "portfolio"],
                "education": ["elearning", "lms", "course", "education"],
                "healthcare": ["medical", "clinic", "doctor", "healthcare"],
                "fitness": ["gym", "workout", "fitness"],
                "travel": ["tourism", "tours", "travel"],
                "creative": ["agency", "studio", "creative"],
                "ecommerce": ["store", "retail", "shop", "electronics", "ecommerce"]
            }

            expanded_cats = synonyms.get(category.lower(), [category.lower()])
            expanded_inds = synonyms.get(industry.lower(), [industry.lower()])

            # Local RAG: semantic query blob + candidate blob for typo/word-order tolerance.
            semantic_query = " ".join(
                [category, industry] + (list(features) or []) + expanded_cats + expanded_inds
            )
            semantic_q_tokens = tokenize(semantic_query)

            results = []
            for row in rows:
                item = dict(row)
                score = 0
                item_cat = item["category"].lower()
                item_ind = item["industry"].lower()
                item_tags = [t.strip().lower() for t in item["tags"].split(",") if t.strip()]
                item_features = [f.strip().lower() for f in item["features"].split(",") if f.strip()]
                item_name = item["name"].lower()

                if item_cat in expanded_cats or category.lower() in item_cat:
                    score += 50
                if item_ind in expanded_inds or industry.lower() in item_ind:
                    score += 30

                for syn in expanded_cats + expanded_inds:
                    if syn in item_name or any(syn in t for t in item_tags):
                        score += 15

                for f in features:
                    if f.lower() in item_features or any(f.lower() in t for t in item_tags):
                        score += 10

                # Semantic bonus (+12 max): catches fuzzy wording the exact matcher misses.
                candidate_tokens = tokenize(
                    " ".join([item_name] + item_tags + item_features + [item_cat, item_ind])
                )
                sem = semantic_similarity(semantic_query, " ".join(candidate_tokens))
                sem += overlap_ratio(semantic_q_tokens, candidate_tokens) * 2
                if score == 0 and sem > 0:
                    score += int(sem * 10)
                elif sem > 0:
                    score += int(sem * 2)
                score += self._usage_bias(item)
                item["score"] = score
                item["semantic_score"] = round(sem, 3)
                results.append(item)

            results.sort(key=lambda x: x["score"], reverse=True)
            self.record_search(
                f"template:{category}:{industry}",
                f"{len(results)} match(es)",
                len(results),
            )
            return results
        except Exception as e:
            agent_logger.error(f"Error searching templates: {e}")
            return []


    def search_components(self, category: str, features: List[str], keywords: List[str]) -> List[Dict[str, Any]]:
        """Search and rank components from local SQLite registry index."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM components_index")
            rows = cursor.fetchall()

            matched = []
            semantic_query = " ".join(
                [category] + (list(features) or []) + (list(keywords) or [])
            )
            semantic_q_tokens = tokenize(semantic_query)
            for row in rows:
                item = dict(row)
                score = 0
                comp_tags = [t.strip().lower() for t in item["tags"].split(",") if t.strip()]
                comp_features = [f.strip().lower() for f in item["features"].split(",") if f.strip()]

                if item["category"].lower() in [category.lower(), "common", "ui"]:
                    score += 20

                for feat in features:
                    if feat.lower() in comp_features or any(feat.lower() in t for t in comp_tags):
                        score += 25

                for kw in keywords:
                    if kw.lower() in item["name"].lower() or any(kw.lower() in t for t in comp_tags):
                        score += 15

                # Semantic bonus: fuzzy feature/name matches that the exact matcher misses.
                candidate_tokens = tokenize(
                    " ".join([item["name"].lower()] + comp_tags + comp_features)
                )
                sem = semantic_similarity(semantic_query, " ".join(candidate_tokens))
                sem += overlap_ratio(semantic_q_tokens, candidate_tokens) * 2
                if score == 0 and sem > 0:
                    score += int(sem * 12)
                elif sem > 0:
                    score += int(sem * 3)
                score += self._usage_bias(item)
                if score > 0:
                    item["score"] = score
                    item["semantic_score"] = round(sem, 3)
                    matched.append(item)

            matched.sort(key=lambda x: x["score"], reverse=True)
            self.record_search(
                f"component:{category}",
                f"{len(matched)} match(es)",
                len(matched),
            )
            return matched
        except Exception as e:
            agent_logger.error(f"Error searching components: {e}")
            return []

    def search_assets(self, industry: str, asset_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve local icons, images, and animations matching industry and category."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assets_index")
            rows = cursor.fetchall()

            categorized = {"images": [], "icons": [], "animations": []}
            for row in rows:
                item = dict(row)
                atype = item["type"]
                if atype == "image":
                    categorized["images"].append(item)
                elif atype == "icon":
                    categorized["icons"].append(item)
                elif atype == "animation":
                    categorized["animations"].append(item)

            self.record_search(
                f"asset:{industry}",
                f"{len(categorized['images'])} images, {len(categorized['icons'])} icons, {len(categorized['animations'])} animations",
                sum(len(v) for v in categorized.values()),
            )
            return categorized
        except Exception as e:
            agent_logger.error(f"Error searching assets: {e}")
            return {"images": [], "icons": [], "animations": []}

    def search_backend(self, category: str, features: List[str]) -> Optional[Dict[str, Any]]:
        """Find best matching backend template and its modules."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM backend_index WHERE category = ?", (category,))
            row = cursor.fetchone()

            if row:
                res = dict(row)
                res["modules"] = [m.strip() for m in res["modules"].split(",") if m.strip()]
                self.record_search(f"backend:{category}", res["name"], 1)
                return res

            cursor.execute("SELECT * FROM backend_index")
            rows = cursor.fetchall()

            if rows:
                res = dict(rows[0])
                res["modules"] = [m.strip() for m in res["modules"].split(",") if m.strip()]
                self.record_search(f"backend:{category}", res["name"], 1)
                return res
            return None
        except Exception as e:
            agent_logger.error(f"Error searching backend: {e}")
            return None

    def search_database_schemas(self, features: List[str], industry: str) -> List[Dict[str, Any]]:
        """Retrieve matching database SQL schemas."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM database_schemas_index")
            rows = cursor.fetchall()

            matched = []
            for row in rows:
                item = dict(row)
                schema_features = [f.strip().lower() for f in item["features"].split(",") if f.strip()]
                score = 0
                for f in features:
                    if f.lower() in schema_features or item["category"].lower() in [f.lower(), industry.lower()]:
                        score += 30
                score += self._usage_bias(item)
                if score > 0 or item["category"] in ["auth", "ecommerce", industry]:
                    item["score"] = score
                    matched.append(item)

            matched.sort(key=lambda x: x["score"], reverse=True)
            self.record_search(
                f"schema:{industry}",
                f"{len(matched)} match(es)",
                len(matched),
            )
            return matched
        except Exception as e:
            agent_logger.error(f"Error searching database schemas: {e}")
            return []

    def record_search(self, query: str, summary: str, matches_count: int, session_id: str = None) -> None:
        """Log search history to database with lock retry logic."""
        q = "INSERT INTO search_history (query, result_summary, matches_count, session_id) VALUES (?, ?, ?, ?)"
        self._execute_write_retry(q, (query, summary, matches_count, session_id))
