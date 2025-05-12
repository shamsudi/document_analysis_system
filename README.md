# Document Analysis System

A FastAPI-based document analysis system that processes PDF and DOCX files, generates embeddings using `nomic-embed-text`, and answers queries using the Mistral 7B language model. The system leverages GPU acceleration for efficient embedding and inference, with a modular architecture including a backend, frontend, vector store (ChromaDB), Redis cache, and Prometheus monitoring.

## Project Structure

- **backend/**: FastAPI backend for document processing and querying.
  - **src/**: Core Python modules.
    - `document_processor.py`: Extracts text, generates embeddings, and stores chunks in the vector store.
    - `monitoring.py`: FastAPI app with endpoints (`/api/health`, `/api/topics`, `/api/query`) and metrics.
    - `vector_store.py`: Interfaces with ChromaDB for vector storage and retrieval.
    - `cache.py`: Redis-based caching for query responses.
    - `config.py`: Configuration settings (e.g., `LLAMA_URL`, `DOCUMENTS_PATH`).
  - `requirements.txt`: Python dependencies.
  - `Dockerfile`: Backend container setup.
- **frontend/**: Web interface for interacting with the backend.
  - `Dockerfile`: Frontend container setup.
- **documents/**: Directory for input documents (e.g., `topic1/sample.pdf`, `topic2/`).
- **chroma_db/**: Persistent storage for ChromaDB vector data.
- **docker-compose.yml**: Defines services (backend, ollama, redis, vector-db, prometheus, frontend).
- **prometheus.yml**: Prometheus configuration for metrics.
- **Makefile**: Automates model downloading and stack startup.
- **README.md**: Project documentation (this file).

## Prerequisites

### Hardware
- NVIDIA GPU (e.g., RTX 3070) with ~8GB VRAM.
- 16GB RAM (12GB allocated to WSL2).
- Multi-core CPU (6+ cores recommended).

### Software
- Windows 10/11 (Pro or Enterprise for WSL2).
- WSL2 with Ubuntu 22.04.
- Docker Desktop with WSL2 integration.
- NVIDIA CUDA drivers (version 12.3 or later).

### Disk Space
- ~10GB for models (`mistral:7b`, `nomic-embed-text`).
- ~5GB for Docker images and volumes.

## Setup Instructions (WSL2 with GPU)

1. **Install WSL2 and Ubuntu**:
   ```bash
   wsl --install
   wsl --install -d Ubuntu-22.04
   wsl --set-default-version 2


1.  **Install NVIDIA CUDA Drivers**:

    -   Download and install NVIDIA drivers for Windows from [NVIDIA's website](https://www.nvidia.com/Download/index.aspx).
    -   Install CUDA Toolkit for WSL2:

        ```
        wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
        sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
        wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda-repo-wsl-ubuntu-12-3-local_12.3.0-1_amd64.deb
        sudo dpkg -i cuda-repo-wsl-ubuntu-12-3-local_12.3.0-1_amd64.deb
        sudo cp /var/cuda-repo-wsl-ubuntu-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
        sudo apt-get update
        sudo apt-get -y install cuda-toolkit-12-3

        ```

    -   Verify:

        ```
        nvidia-smi

        ```

2.  **Install Docker Desktop**:

    -   Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
    -   Enable WSL2 integration in Docker Desktop > Settings > Resources > WSL Integration.
    -   Install Docker CLI in WSL:

        ```
        sudo apt-get update
        sudo apt-get install -y docker.io
        sudo usermod -aG docker $USER

        ```

    -   Verify:

        ```
        docker run --rm hello-world

        ```

3.  **Clone the Repository**:

    ```
    git clone <repository-url>
    cd document-analysis-system

    ```

4.  **Configure WSL2 Resources**:

    -   Create/edit `~/.wslconfig` in Windows (e.g., `C:\Users\<YourUser>\.wslconfig`):

        ```
        [wsl2]
        memory=12GB
        processors=6
        swap=8GB

        ```

    -   Restart WSL:

        ```
        wsl --shutdown

        ```

Running the Application
-----------------------

1.  **Download Models and Start Services**:

    ```
    make start

    ```

    -   This runs `Makefile` to:
        -   Pull `nomic-embed-text:latest` and `mistral:7b-instruct-v0.3-q4_0`.
        -   Build and start all services via `docker-compose.yml`.
2.  **Verify Services** (after ~5 minutes):

    ```
    docker compose ps

    ```

    -   Ensure all services (`backend-1`, `ollama-1`, etc.) are healthy.
3.  **Test Endpoints**:

    ```
    curl http://localhost:8000/api/health
    curl http://localhost:8000/api/topics
    curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" -d '{"question":"Summarize the chapter on AI in the document","topics":["topic1"]}'

    ```

4.  **Access Frontend**:

    -   Open `http://localhost` in a browser.
5.  **Monitor Metrics**:

    -   Prometheus: `http://localhost:9090`.

Modules and Technologies
------------------------

-   **Backend**: FastAPI with LangChain for document processing and querying.
-   **LLM/Embedding**: Ollama with `mistral:7b-instruct-v0.3-q4_0` (LLM) and `nomic-embed-text` (embeddings), GPU-accelerated.
-   **Vector Store**: ChromaDB for storing document embeddings.
-   **Cache**: Redis for caching query responses.
-   **Monitoring**: Prometheus for system metrics (CPU, memory, request latency).
-   **Frontend**: Web interface (details in `frontend/`).
-   **Orchestration**: Docker Compose for service management.

Notes
-----

-   **Documents**: Place PDF/DOCX files in `documents/<topic>/` (e.g., `documents/topic1/sample.pdf`). The folder structure is included in the repository, but actual files are excluded via `.gitignore`.
-   **Performance**: GPU acceleration reduces embedding time for 206 chunks from ~26 minutes (CPU) to ~13-26 seconds.
-   **Troubleshooting**:
    -   Check GPU usage:

        ```
        docker compose exec ollama nvidia-smi

        ```

    -   View logs:

        ```
        docker compose logs --follow backend

        ```

    -   Verify models:

        ```
        docker compose exec ollama ollama list

        ```

```
