# Phase 1 Guide: Architecture, Registry & Memory Engine

## 1. Architecture Overview
LumicorePro Core uses a local-first memory and registry architecture storing component metadata in JSON catalogs (`registry/*.json`) and an indexed SQLite database (`ai-agent/database/agent.db`).

## 2. SQLite Initialization
To initialize or seed the local memory database:
```bash
python ai-agent/database/init_db.py
```
This automatically enables SQLite WAL mode (`PRAGMA journal_mode=WAL;`) and creates indexes for templates, components, assets, backends, and SQL schemas.
