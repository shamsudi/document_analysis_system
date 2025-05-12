import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.config import settings
from src.cache import Cache
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStore
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time
from threading import Thread
from langchain.chains import RetrievalQA
import psutil
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    question: str
    topics: list[str]

logger.debug("Initializing FastAPI app")
app = FastAPI(
    title="Document Analysis API",
    description="API for querying documents using Mistral 7B",
    version="1.0.0"
)
logger.debug("FastAPI app initialized")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.debug("Initializing Cache")
cache = Cache()
logger.debug("Initializing DocumentProcessor")
processor = DocumentProcessor()
logger.debug("Initializing VectorStore")
vector_store = VectorStore(settings.VECTOR_DB_URL)
logger.debug("Global initializations complete")

METRICS_NAMESPACE = "document_analysis"
REQUESTS = Counter(f"{METRICS_NAMESPACE}_requests_total", "Total number of incoming requests")
EXCEPTIONS = Counter(f"{METRICS_NAMESPACE}_exceptions_total", "Total number of exceptions raised")
PROCESSING_TIME = Histogram(f"{METRICS_NAMESPACE}_processing_seconds", "Time spent processing requests")
CACHE_HITS = Counter(f"{METRICS_NAMESPACE}_cache_hits_total", "Number of successful cache retrievals")
CACHE_MISSES = Counter(f"{METRICS_NAMESPACE}_cache_misses_total", "Number of cache misses")
SYSTEM_CPU_USAGE = Gauge(f"{METRICS_NAMESPACE}_system_cpu_usage", "System CPU usage percentage")
SYSTEM_MEMORY_USAGE = Gauge(f"{METRICS_NAMESPACE}_system_memory_usage", "System memory usage percentage")
CACHE_HIT_RATIO = Gauge(f"{METRICS_NAMESPACE}_cache_hit_ratio", "Cache hit ratio")

def update_system_metrics():
    while True:
        SYSTEM_CPU_USAGE.set(psutil.cpu_percent())
        SYSTEM_MEMORY_USAGE.set(psutil.virtual_memory().percent)
        CACHE_HIT_RATIO.set(cache.hit_ratio())
        time.sleep(1)

def start_metrics_server(port: int = 8001) -> None:
    logger.info(f"Starting metrics server on port {port}")
    start_http_server(port)
    logger.info("Metrics server started successfully")

def instrument_endpoint(endpoint_name: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            REQUESTS.inc()
            try:
                result = await func(*args, **kwargs)
                PROCESSING_TIME.observe(time.perf_counter() - start_time)
                return result
            except Exception as e:
                EXCEPTIONS.inc()
                raise e
        return wrapper
    return decorator

async def process_documents_background():
    logger.debug("Starting background document processing")
    try:
        await asyncio.sleep(60)  # Delay 1 minute for GPU model loading
        processor.process_directory(settings.DOCUMENTS_PATH)
        logger.info("Background document processing completed")
    except Exception as e:
        logger.error(f"Background document processing failed: {str(e)}")

@app.on_event("startup")
@instrument_endpoint()
async def startup_event():
    logger.debug("Starting document analysis system initialization")
    # Start metrics server immediately
    start_metrics_server()
    logger.debug("Metrics server started")
    metrics_thread = Thread(target=update_system_metrics, daemon=True)
    metrics_thread.start()
    logger.debug("Background metrics collection started")
    # Schedule document processing as a background task
    asyncio.create_task(process_documents_background())
    logger.debug("Background document processing task scheduled")

@app.get("/api/health")
@instrument_endpoint()
async def health_check():
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

@app.get("/api/topics")
@instrument_endpoint()
async def get_topics():
    try:
        topics = processor.get_topics()
        logger.debug(f"Retrieved topics: {topics}")
        return {"topics": topics}
    except Exception as e:
        logger.error(f"Failed to retrieve topics: {str(e)}")
        raise HTTPException(status_code=500, detail="Topic retrieval failed")

@app.post("/api/query")
@instrument_endpoint()
async def query(query_request: QueryRequest):
    try:
        cache_key = f"query:{query_request.question}:{','.join(query_request.topics)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            CACHE_HITS.inc()
            logger.info("Serving response from cache")
            return {"answer": cached_response}
        CACHE_MISSES.inc()
        
        search_kwargs = {"filter": {"topic": {"$in": query_request.topics}}} if query_request.topics else {}
        retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
        qa_chain = RetrievalQA.from_chain_type(
            llm=processor.llm,
            chain_type='stuff',
            retriever=retriever,
            verbose=True
        )
        answer = qa_chain.run(query_request.question)
        cache.set(cache_key, answer)
        logger.info("Query processed and cached")
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Query processing failed")