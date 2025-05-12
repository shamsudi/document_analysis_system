import logging
logging.basicConfig(level=logging.DEBUG)
from src.document_processor import DocumentProcessor
from src.config import settings
try:
    logger = logging.getLogger(__name__)
    logger.debug("Initializing DocumentProcessor")
    processor = DocumentProcessor()
    logger.debug("Processing documents")
    processor.process_directory(settings.DOCUMENTS_PATH)
    logger.debug("Document processing successful")
except Exception as e:
    logger.error(f"Error: {e}")
    raise
