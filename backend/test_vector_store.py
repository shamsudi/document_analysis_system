import logging
logging.basicConfig(level=logging.DEBUG)
from src.vector_store import VectorStore
try:
    vector_store = VectorStore("http://vector-db:8000")
    print("VectorStore initialized successfully")
except Exception as e:
    print(f"Error initializing VectorStore: {e}")
    raise
