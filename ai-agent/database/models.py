from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class TemplateItem:
    name: str
    type: str
    category: str
    industry: str
    tags: List[str]
    description: str
    file_path: str
    dependencies: List[str]
    compatible_categories: List[str]
    features: List[str]
    rating: float = 5.0
    id: Optional[int] = None

@dataclass
class ComponentItem:
    name: str
    type: str
    category: str
    tags: List[str]
    description: str
    file_path: str
    dependencies: List[str]
    compatible_categories: List[str]
    features: List[str]
    id: Optional[int] = None

@dataclass
class AssetItem:
    name: str
    type: str  # image, icon, animation
    category: str
    industry: str
    tags: List[str]
    file_path: str
    id: Optional[int] = None

@dataclass
class BackendModuleItem:
    name: str
    type: str
    category: str
    tags: List[str]
    description: str
    file_path: str
    modules: List[str]
    dependencies: List[str]
    id: Optional[int] = None

@dataclass
class DatabaseSchemaItem:
    name: str
    type: str
    category: str
    file_path: str
    tables: List[str]
    features: List[str]
    id: Optional[int] = None

@dataclass
class GenerationRecord:
    project_name: str
    prompt: str
    template_used: str
    status: str
    report_json: str
    created_at: Optional[str] = None
    id: Optional[int] = None
