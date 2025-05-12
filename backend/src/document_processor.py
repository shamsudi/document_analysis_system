import os
import logging
from typing import List, Dict, Any
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from .config import settings
from .vector_store import VectorStore
from pypdf import PdfReader
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Processes PDF and DOCX documents, extracting text and generating embeddings.
    
    Attributes:
        llm (OllamaLLM): Language model for processing
        embeddings (OllamaEmbeddings): Embedding model
        vector_store (VectorStore): Custom vector store for document storage
        topics (set): Set of unique topics found in documents
    """
    def __init__(self):
        """
        Initialize the document processor with language model, embeddings, and vector store.
        """
        logger.debug("Initializing OllamaLLM with model=mistral:7b-instruct-v0.3-q4_0")
        self.llm = OllamaLLM(
            base_url=settings.LLAMA_URL,
            model="mistral:7b-instruct-v0.3-q4_0",  # Switched to Mistral 7B
            verbose=True
        )
        logger.debug("Initializing OllamaEmbeddings with model=nomic-embed-text")
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=settings.LLAMA_URL
        )
        logger.debug("Initializing VectorStore")
        self.vector_store = VectorStore(settings.VECTOR_DB_URL)
        logger.debug(f"VectorStore initialized: {type(self.vector_store).__name__}, has add_texts: {hasattr(self.vector_store, 'add_texts')}")
        self.topics = set()  # Track unique topics

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text
        """
        try:
            with open(file_path, 'rb') as file:
                pdf = PdfReader(file)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {str(e)}")
            return ""

    def _extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from a DOCX file.
        
        Args:
            file_path (str): Path to the DOCX file
            
        Returns:
            str: Extracted text
        """
        try:
            doc = DocxDocument(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX {file_path}: {str(e)}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 4000) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text (str): Input text to chunk
            chunk_size (int): Maximum size of each chunk
            
        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    def _process_single_file(self, file_path: str, topic: str) -> int:
        """
        Process a single file (PDF or DOCX) and store in vector store.
        
        Args:
            file_path (str): Path to the file
            topic (str): Topic associated with the file
            
        Returns:
            int: Number of chunks processed
        """
        logger.debug(f"Processing file: {file_path} with topic: {topic}")
        try:
            if file_path.endswith('.pdf'):
                logger.debug(f"Extracting text from PDF: {file_path}")
                text = self._extract_text_from_pdf(file_path)
            elif file_path.endswith('.docx'):
                logger.debug(f"Extracting text from DOCX: {file_path}")
                text = self._extract_text_from_docx(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return 0
                
            if not text:
                logger.warning(f"No text extracted from {file_path}")
                return 0
                
            logger.debug(f"Chunking text from {file_path}")
            chunks = self._chunk_text(text)
            metadatas = [{"text": chunk, "topic": topic} for chunk in chunks]
            
            logger.debug(f"Adding {len(chunks)} chunks to vector store for {file_path}")
            self.vector_store.add_texts(chunks, metadatas, batch_size=16)  # Increased for GPU
            logger.info(f"Successfully processed {file_path}, {len(chunks)} chunks")
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}")
            return 0

    def process_directory(self, directory_path: str) -> None:
        """
        Process all PDF and DOCX files in the specified directory.
        
        Args:
            directory_path (str): Path to the directory containing documents
        """
        try:
            for root, _, files in os.walk(directory_path):
                topic = os.path.basename(root)
                if topic != os.path.basename(directory_path):  # Skip root directory
                    self.topics.add(topic)
                for file in files:
                    if file.endswith(('.pdf', '.docx')):
                        chunk_count = self._process_single_file(os.path.join(root, file), topic)
                        logger.info(f"Processed file: {file}, {chunk_count} chunks")
        except Exception as e:
            logger.error(f"Failed to process directory {directory_path}: {str(e)}")

    def get_topics(self) -> List[str]:
        """
        Retrieve all unique topics found in processed documents.
        
        Returns:
            List[str]: List of unique topic names
        """
        return sorted(self.topics)