import logging
logging.basicConfig(level=logging.DEBUG)
from src.monitoring import app, cache, processor, vector_store
print("All imports and initializations successful")
