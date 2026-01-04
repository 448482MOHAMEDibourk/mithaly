"""Ingest script to populate Vector Memory via KnowledgeManager."""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from mithaly.core.memory.knowledge_manager import KnowledgeManager
except ImportError:
    print("ERROR: Could not import KnowledgeManager. Make sure you are in project root.")
    sys.exit(1)

def ingest_directory(path: str):
    km = KnowledgeManager()
    
    print(f"Scanning {path}...")
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(('.md', '.txt', '.py')):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content) < 50: continue
                    
                    # Naive chunking
                    chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
                    
                    for i, chunk in enumerate(chunks):
                        # Infer topic from directory or filename logic
                        topics = ["documentation"]
                        if "core" in full_path: topics.append("core")
                        if "adapter" in full_path: topics.append("adapter")
                        
                        km.log_knowledge(
                            content=chunk,
                            topics=topics,
                            provenance=full_path,
                            trusted=True,
                            metadata={"chunk": i}
                        )
                        
                except Exception as e:
                    print(f"Skipping {file}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "docs"
    
    ingest_directory(target)
