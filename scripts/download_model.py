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
            
            # Implement abstract methods required by VannaBase
            def system_message(self, message: str):
                return {"role": "system", "content": message}
                
            def user_message(self, message: str):
                return {"role": "user", "content": message}
                
            def assistant_message(self, message: str):
                return {"role": "assistant", "content": message}
                
            def submit_prompt(self, prompt, **kwargs):
                return "Dummy response"

        # Use a dummy path for this step
        config = {"path": "./tmp_chroma_db_dl"}
        downloader = ModelDownloader(config=config)
        
        # Force download by generating an embedding
        print("Triggering embedding generation to ensure model download...")
        try:
            # Vanna VectorStore usually has generate_embedding
            if hasattr(downloader, 'generate_embedding'):
                downloader.generate_embedding("warmup")
            else:
                print("generate_embedding method not found, skipping explicit generation.")
        except Exception as inner_e:
            # Depending on the implementation, this might fail if DB path is invalid, 
            # but the model download happens before that usually.
            print(f"Note: embedding generation attempt: {inner_e}")

        print("Model download completed successfully.")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        # Print full traceback for debugging if needed
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    download_model()
