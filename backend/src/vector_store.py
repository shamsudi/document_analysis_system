import os
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from .config import settings
import logging
import chromadb

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store implementation using Chroma for document storage and retrieval.
    
    Attributes:
        vector_db_url (str): URL for the Chroma instance
        embedding (OllamaEmbeddings): Embedding model for text
        vector_store (Chroma): Chroma vector store instance
    """
    def __init__(self, vector_db_url: str):
        """
        Initialize the vector store with Chroma connection.
        
        Args:
            vector_db_url (str): URL for the Chroma instance (e.g., http://vector-db:8000)
        """
        self.vector_db_url = vector_db_url
        self.embedding = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=settings.LLAMA_URL
        )
        try:
            # Connect to the external Chroma instance
            client = chromadb.HttpClient(
                host="vector-db",
                port=8000,
                tenant="default_tenant",
                database="default_database",
                settings=chromadb.config.Settings(allow_reset=True)
            )
            self.vector_store = Chroma(
                collection_name="documents",
                embedding_function=self.embedding,
                client=client,
                collection_metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            logger.info(f"Initialized Chroma vector store with collection 'documents' at {vector_db_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma vector store: {str(e)}")
            raise

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]], batch_size: int = 8) -> None:
        """
        Add texts with metadata to the vector store in batches.
        
        Args:
            texts (List[str]): List of text chunks to store
            metadatas (List[Dict[str, Any]]): List of metadata dictionaries for each text
            batch_size (int): Number of texts to process in each batch
        """
        try:
            logger.debug(f"Adding {len(texts)} texts in batches of {batch_size}")
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = [f"doc_{i+j}" for j in range(len(batch_texts))]
                logger.debug(f"Processing batch {i//batch_size + 1} with {len(batch_texts)} texts")
                self.vector_store.add_texts(
                    texts=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                logger.info(f"Added {len(batch_texts)} texts to Chroma vector store (batch {i//batch_size + 1})")
        except Exception as e:
            logger.error(f"Failed to add texts to vector store: {str(e)}")
            raise
    
    def query(self, query_text: str, top_k: int = 5, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar texts.
        
        Args:
            query_text (str): Query text to search for
            top_k (int): Number of top results to return
            filter (Dict[str, Any], optional): Metadata filter for the query
            
        Returns:
            List[Dict[str, Any]]: List of matching documents with scores
        """
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query_text,
                k=top_k,
                filter=filter or {}
            )
            return [
                {"text": doc.metadata.get("text", ""), "score": score}
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Vector store query failed: {str(e)}")
            return []

    def get_topics(self) -> List[str]:
        """
        Retrieve all unique topics from the document processor.
        
        Returns:
            List[str]: List of unique topic names
        """
        try:
            from .document_processor import DocumentProcessor
            return DocumentProcessor().get_topics()
        except Exception as e:
            logger.error(f"Failed to retrieve topics: {str(e)}")
            return []

    def as_retriever(self, search_kwargs: Dict[str, Any] = None) -> Any:
        """
        Return the vector store as a LangChain retriever.
        
        Args:
            search_kwargs (Dict[str, Any], optional): Search parameters for the retriever
            
        Returns:
            Any: LangChain retriever object
        """
        return self.vector_store.as_retriever(
            search_kwargs=search_kwargs or {}
        )