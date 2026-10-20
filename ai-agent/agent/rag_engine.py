"""
RAG Engine - Retrieval-Augmented Generation
============================================
Advanced context retrieval system using vector embeddings for intelligent code generation.

Features:
- ChromaDB vector storage for documentation & code snippets
- Semantic search for relevant context
- Persistent knowledge base
- Auto-update from project files
- Multi-source retrieval (docs, code, examples)
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[WARNING] ChromaDB not available. Install with: pip install chromadb")
try:
    # Optional quality upgrade — chroma's built-in ONNX MiniLM is used instead
    # when sentence-transformers/torch is not installed. All add()/query()
    # paths below rely on the collection's default embedding function, so the
    # agent's RAG works with just `pip install chromadb`.
    from sentence_transformers import SentenceTransformer
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False

from utils.logger import agent_logger


class RAGEngine:
    """Retrieval-Augmented Generation engine for context-aware code generation."""
    
    def __init__(self, persist_dir: Optional[str] = None):
        """Initialize RAG engine with optional persistent storage."""
        self.persist_dir = Path(persist_dir or Path(__file__).parent.parent / "database" / "rag_store")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.enabled = CHROMADB_AVAILABLE and os.getenv("RAG_ENABLED", "true").lower() == "true"
        
        if not self.enabled:
            agent_logger.info("RAG engine disabled or dependencies missing")
            return
            
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collections
            self.docs_collection = self.client.get_or_create_collection(
                name="documentation",
                metadata={"description": "Technical documentation and best practices"}
            )
            
            self.code_collection = self.client.get_or_create_collection(
                name="code_snippets",
                metadata={"description": "Reusable code patterns and components"}
            )
            
            self.examples_collection = self.client.get_or_create_collection(
                name="examples",
                metadata={"description": "Complete project examples and templates"}
            )
            
            # Initialize embedding model only when sentence-transformers is
            # present; otherwise Chroma's built-in ONNX MiniLM default keeps
            # the same pipeline torch-free.
            if _SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            else:
                self.embedding_model = None
            
            agent_logger.info(f"RAG engine initialized with {self._get_stats()}")
            
        except Exception as e:
            agent_logger.error(f"Failed to initialize RAG engine: {e}")
            self.enabled = False
    
    def _get_stats(self) -> str:
        """Get collection statistics."""
        if not self.enabled:
            return "disabled"
        try:
            docs_count = self.docs_collection.count()
            code_count = self.code_collection.count()
            examples_count = self.examples_collection.count()
            return f"{docs_count} docs, {code_count} snippets, {examples_count} examples"
        except:
            return "unknown"
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content hash."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_documentation(self, title: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add documentation to the knowledge base."""
        if not self.enabled:
            return False
            
        try:
            doc_id = self._generate_id(f"{title}:{content[:100]}")
            
            self.docs_collection.add(
                documents=[content],
                metadatas=[{
                    "title": title,
                    "type": "documentation",
                    **(metadata or {})
                }],
                ids=[doc_id]
            )
            
            agent_logger.debug(f"Added documentation: {title}")
            return True
            
        except Exception as e:
            agent_logger.error(f"Failed to add documentation: {e}")
            return False
    
    def add_code_snippet(self, name: str, code: str, language: str, 
                         description: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
        """Add code snippet to the knowledge base."""
        if not self.enabled:
            return False
            
        try:
            snippet_id = self._generate_id(f"{name}:{code[:100]}")
            
            # Combine code with description for better semantic search
            searchable_content = f"{name}\n{description or ''}\n{code}"
            
            self.code_collection.add(
                documents=[searchable_content],
                metadatas=[{
                    "name": name,
                    "language": language,
                    "description": description or "",
                    "tags": ",".join(tags or []),
                    "code": code  # Store actual code in metadata
                }],
                ids=[snippet_id]
            )
            
            agent_logger.debug(f"Added code snippet: {name}")
            return True
            
        except Exception as e:
            agent_logger.error(f"Failed to add code snippet: {e}")
            return False
    
    def add_example_project(self, project_name: str, description: str, 
                           tech_stack: List[str], structure: Dict, 
                           key_files: Optional[Dict[str, str]] = None) -> bool:
        """Add complete project example to the knowledge base."""
        if not self.enabled:
            return False
            
        try:
            project_id = self._generate_id(project_name)
            
            # Create searchable content
            content = f"{project_name}\n{description}\nTech: {', '.join(tech_stack)}\n"
            if key_files:
                content += "\n".join([f"{path}: {snippet[:200]}" for path, snippet in key_files.items()])
            
            self.examples_collection.add(
                documents=[content],
                metadatas=[{
                    "project_name": project_name,
                    "description": description,
                    "tech_stack": ",".join(tech_stack),
                    "structure": json.dumps(structure),
                    "key_files": json.dumps(key_files or {})
                }],
                ids=[project_id]
            )
            
            agent_logger.debug(f"Added example project: {project_name}")
            return True
            
        except Exception as e:
            agent_logger.error(f"Failed to add example project: {e}")
            return False
    
    def search_documentation(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search documentation by semantic similarity."""
        if not self.enabled:
            return []
            
        try:
            results = self.docs_collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            return self._format_results(results)
            
        except Exception as e:
            agent_logger.error(f"Documentation search failed: {e}")
            return []
    
    def search_code(self, query: str, language: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search code snippets by semantic similarity."""
        if not self.enabled:
            return []
            
        try:
            where_filter = {"language": language} if language else None
            
            results = self.code_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )
            
            # Extract actual code from metadata
            formatted = self._format_results(results)
            for item in formatted:
                if "code" in item["metadata"]:
                    item["code"] = item["metadata"]["code"]
            
            return formatted
            
        except Exception as e:
            agent_logger.error(f"Code search failed: {e}")
            return []
    
    def search_examples(self, query: str, tech_stack: Optional[List[str]] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search example projects by semantic similarity."""
        if not self.enabled:
            return []
            
        try:
            results = self.examples_collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            formatted = self._format_results(results)
            
            # Parse JSON fields
            for item in formatted:
                if "structure" in item["metadata"]:
                    try:
                        item["structure"] = json.loads(item["metadata"]["structure"])
                    except:
                        pass
                if "key_files" in item["metadata"]:
                    try:
                        item["key_files"] = json.loads(item["metadata"]["key_files"])
                    except:
                        pass
            
            return formatted
            
        except Exception as e:
            agent_logger.error(f"Example search failed: {e}")
            return []
    
    def get_context_for_prompt(self, prompt: str, max_context_length: int = 2000) -> str:
        """Get relevant context from all knowledge bases for a prompt."""
        if not self.enabled:
            return ""
            
        try:
            context_parts = []
            
            # Search documentation
            docs = self.search_documentation(prompt, top_k=2)
            if docs:
                context_parts.append("## Relevant Documentation:")
                for doc in docs:
                    title = doc["metadata"].get("title", "Untitled")
                    content = doc["document"][:500]  # Limit length
                    context_parts.append(f"\n### {title}\n{content}")
            
            # Search code snippets
            code = self.search_code(prompt, top_k=3)
            if code:
                context_parts.append("\n## Relevant Code Patterns:")
                for snippet in code:
                    name = snippet["metadata"].get("name", "Untitled")
                    desc = snippet["metadata"].get("description", "")
                    code_content = snippet.get("code", snippet["document"])[:400]
                    context_parts.append(f"\n### {name}\n{desc}\n```\n{code_content}\n```")
            
            # Join and compress (Headroom, env-gated; no-op when disabled)
            from utils.context_tools import compress_context
            full_context = compress_context("\n".join(context_parts), max_chars=max_context_length)
            return full_context
            
        except Exception as e:
            agent_logger.error(f"Failed to get context: {e}")
            return ""
    
    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB results into a clean list."""
        formatted = []
        
        if not results or not results.get("documents"):
            return formatted
        
        documents = results["documents"][0]  # First query result
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        for i, doc in enumerate(documents):
            formatted.append({
                "id": ids[i] if i < len(ids) else None,
                "document": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
                "relevance_score": 1 - (distances[i] if i < len(distances) else 0)  # Convert distance to score
            })
        
        return formatted
    
    def index_project_files(self, project_dir: Path, extensions: List[str] = [".js", ".jsx", ".ts", ".tsx", ".py", ".css"]) -> int:
        """Index all code files from a generated project for future reference."""
        if not self.enabled:
            return 0
            
        indexed_count = 0
        
        try:
            for ext in extensions:
                for file_path in project_dir.rglob(f"*{ext}"):
                    if "node_modules" in str(file_path) or "__pycache__" in str(file_path):
                        continue
                    
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        relative_path = file_path.relative_to(project_dir)
                        
                        # Determine language
                        lang_map = {".js": "javascript", ".jsx": "javascript", 
                                   ".ts": "typescript", ".tsx": "typescript",
                                   ".py": "python", ".css": "css"}
                        language = lang_map.get(ext, ext[1:])
                        
                        # Add to knowledge base
                        success = self.add_code_snippet(
                            name=str(relative_path),
                            code=content,
                            language=language,
                            description=f"Generated file from {project_dir.name}",
                            tags=["generated", project_dir.name, language]
                        )
                        
                        if success:
                            indexed_count += 1
                            
                    except Exception as e:
                        agent_logger.debug(f"Could not index {file_path}: {e}")
            
            agent_logger.info(f"Indexed {indexed_count} files from {project_dir.name}")
            return indexed_count
            
        except Exception as e:
            agent_logger.error(f"Project indexing failed: {e}")
            return indexed_count
    
    def seed_best_practices(self):
        """Seed the knowledge base with best practices and common patterns."""
        if not self.enabled:
            return
        
        # React best practices
        self.add_documentation(
            title="React Component Best Practices",
            content="""
            - Use functional components with hooks
            - Keep components small and focused (Single Responsibility)
            - Use PropTypes or TypeScript for type safety
            - Memoize expensive computations with useMemo
            - Avoid inline function definitions in JSX (use useCallback)
            - Use proper key props in lists
            - Handle loading and error states
            - Implement proper accessibility (ARIA labels, semantic HTML)
            """,
            metadata={"category": "react", "type": "best-practices"}
        )
        
        # Performance patterns
        self.add_code_snippet(
            name="Lazy Loading Component",
            code="""
import { lazy, Suspense } from 'react';
import LoadingSpinner from './LoadingSpinner';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <HeavyComponent />
    </Suspense>
  );
}
            """,
            language="javascript",
            description="React lazy loading pattern for code splitting",
            tags=["react", "performance", "lazy-loading"]
        )
        
        # Security patterns
        self.add_documentation(
            title="Frontend Security Best Practices",
            content="""
            - Sanitize user input to prevent XSS attacks
            - Use HTTPS for all API calls
            - Implement Content Security Policy (CSP) headers
            - Store sensitive tokens in httpOnly cookies, not localStorage
            - Validate and sanitize all form inputs
            - Use CSRF tokens for state-changing operations
            - Implement rate limiting on client side
            - Never expose API keys in frontend code
            """,
            metadata={"category": "security", "type": "best-practices"}
        )
        
        agent_logger.info("Seeded best practices into RAG knowledge base")


# Global RAG engine instance
_rag_engine: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    """Get or create the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
        # Seed best practices on first initialization
        if _rag_engine.enabled and _rag_engine.docs_collection.count() == 0:
            _rag_engine.seed_best_practices()
    return _rag_engine
