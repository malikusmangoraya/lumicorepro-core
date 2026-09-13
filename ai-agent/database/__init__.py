"""LumicorePro AI agent database layer.

Exposes the SQLite-backed registry (templates, components, assets, backend
modules, database schemas), the pipeline store (generation runs) and the
accounts store used by the agent. Data-model dataclasses and bootstrap:
  - models.py          dataclasses for registry records
  - init_db.py         schema bootstrap + seeding from registry/*.json
  - pipeline_store.py  generation/pipeline run persistence
  - accounts_store.py  user/account persistence
"""
from .init_db import init_database
from .models import (
    TemplateItem,
    ComponentItem,
    AssetItem,
    BackendModuleItem,
    DatabaseSchemaItem,
    GenerationRecord,
)
from .pipeline_store import PipelineStore

__all__ = [
    "init_database",
    "TemplateItem",
    "ComponentItem",
    "AssetItem",
    "BackendModuleItem",
    "DatabaseSchemaItem",
    "GenerationRecord",
    "PipelineStore",
]