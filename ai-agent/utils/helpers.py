import json
import re
from typing import Any, Dict, List, Union

def normalize_text(text: str) -> str:
    """Normalize string by converting to lowercase, removing non-alphanumeric chars."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    return " ".join(text.split())

def extract_keywords(prompt: str) -> List[str]:
    """Extract clean keywords from a user prompt for registry and local searching."""
    normalized = normalize_text(prompt)
    stopwords = {
        "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
        "which", "this", "that", "these", "those", "then", "just", "so", "than",
        "such", "both", "through", "about", "for", "is", "of", "to", "in", "with",
        "create", "build", "generate", "make", "website", "web", "site", "app",
        "application", "project", "need", "want", "please", "using", "like"
    }
    tokens = normalized.split()
    return [t for t in tokens if t not in stopwords and len(t) > 1]

def safe_json_parse(json_str: str) -> Dict[str, Any]:
    """Parse JSON string safely handling code fences and markdown blocks."""
    if not json_str:
        return {}
    clean_str = json_str.strip()
    if clean_str.startswith("```json"):
        clean_str = clean_str[7:]
    elif clean_str.startswith("```"):
        clean_str = clean_str[3:]
    if clean_str.endswith("```"):
        clean_str = clean_str[:-3]
    clean_str = clean_str.strip()
    try:
        return json.loads(clean_str)
    except Exception:
        # Try finding first { and last }
        start = clean_str.find("{")
        end = clean_str.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(clean_str[start : end + 1])
            except Exception:
                pass
        return {}

def slugify(text: str) -> str:
    """Convert text into URL/folder safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)
