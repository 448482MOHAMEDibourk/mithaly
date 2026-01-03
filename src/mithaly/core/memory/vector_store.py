"""VectorStore - Adapter for Semantic Memory (RAG) using ChromaDB.

This component manages the storage and retrieval of semantic context.
It uses ChromaDB's default local embedding model (all-MiniLM-L6-v2).
"""
import os
import uuid
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

class VectorStore:
    """Manages semantic memory using ChromaDB."""

    def __init__(self, persistence_path: str = "docs/knowledge/chroma_db", collection_name: str = "mithaly_memory"):
        self.client = None
        self.collection = None
        
        if not chromadb:
            print("WARN: 'chromadb' not installed. RAG disabled.")
            return

        try:
            # Ensure directory exists
            os.makedirs(persistence_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=persistence_path)
            self.collection = self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            print(f"ERROR: Failed to initialize ChromaDB: {e}")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]] = None):
        """Add documents to the vector store."""
        if not self.collection:
            return

        count = len(documents)
        ids = [str(uuid.uuid4()) for _ in range(count)]
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in range(count)]
            
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"INFO: Added {count} documents to memory.")
        except Exception as e:
            print(f"ERROR: Failed to add documents: {e}")

    def search(self, query: str, n_results: int = 3) -> List[str]:
        """Search for relevant documents."""
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            # results['documents'] is a list of lists (one per query)
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"ERROR: Vector search failed: {e}")
            return []
