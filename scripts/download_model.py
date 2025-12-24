import os
import sys

def download_model():
    print("Starting embedding model download...")
    try:
        try:
            from vanna.chromadb import ChromaDB_VectorStore
        except ImportError:
            from vanna.legacy.chromadb.chromadb_vector import ChromaDB_VectorStore
            
        # We don't need a real path for the DB, just need to init the class to trigger model download
        # The model is downloaded to ~/.cache/chroma by default
        class ModelDownloader(ChromaDB_VectorStore):
            def __init__(self, config=None):
                # Only init ChromaDB part
                ChromaDB_VectorStore.__init__(self, config=config)

        # Use a dummy path for this step
        config = {"path": "./tmp_chroma_db_dl"}
        ModelDownloader(config=config)
        print("Model download completed successfully.")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()

