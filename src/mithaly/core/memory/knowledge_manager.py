"""KnowledgeManager - The Central Nervous System of Mithaly's Memory.

This module implements the "Hybrid Memory" architecture:
1.  **Source of Truth**: A JSONL ledger (`knowledge.jsonl`) storing all knowledge with metadata.
2.  **Search Index**: ChromaDB for semantic retrieval.
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from mithaly.core.memory.vector_store import VectorStore
except ImportError:
    # Local import fallback if running as script
    import sys
    sys.path.append(os.getcwd() + '/src')
    from mithaly.core.memory.vector_store import VectorStore

class KnowledgeManager:
    """Manages the lifecycle of knowledge: Logging, Indexing, and Retrieval."""

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.ledger_path = os.path.join(project_root, "docs/context/knowledge.jsonl")
        self.vector_store = VectorStore()
        
        # Ensure context dir exists
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)

    def log_knowledge(self, 
                      content: str, 
                      topics: List[str], 
                      provenance: str = "system", 
                      trusted: bool = True,
                      metadata: Dict[str, Any] = None) -> str:
        """
        Log a piece of knowledge to the ledger and index it.
        Returns the Record ID.
        """
        record_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        record = {
            "id": record_id,
            "ts": timestamp,
            "topics": topics,
            "content": content,
            "provenance": provenance,
            "trusted": trusted,
            "metadata": metadata or {}
        }

        # 1. Write to Ledger (JSONL)
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            print(f"INFO: Logged knowledge record {record_id} to ledger.")
        except Exception as e:
            print(f"ERROR: Failed to write to ledger: {e}")
            return None

        # 2. Index in VectorStore (if trusted or desired)
        # We generally index everything so we can find it, but maybe we filter queries later.
        if self.vector_store:
            # Metadata for Chroma
            v_meta = {
                "source": "knowledge_ledger",
                "record_id": record_id,
                "topics": ",".join(topics),
                "trusted": str(trusted),
                "provenance": provenance
            }
            # Add topic to content for better semantic match
            v_content = f"Topics: {', '.join(topics)}\nContent: {content}"
            self.vector_store.add_documents([v_content], [v_meta])

        return record_id

    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search for knowledge. 
        Returns list of records (either from VectorDB or fetched from Ledger if needed).
        For now, returns the content string from VectorDB to save IO.
        """
        if not self.vector_store:
            return []
            
        # Raw docs from Chroma
        docs = self.vector_store.search(query, n_results)
        # TODO: In full implementation, we might fetch the full JSON from ledger using ID.
        # For now, the vector store content is sufficient context.
        return docs
