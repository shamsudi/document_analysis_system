# Makefile for Document Analysis System

# Variables
COMPOSE_FILE = docker-compose.yml
OLLAMA_SERVICE = ollama
MODELS = nomic-embed-text:latest mistral:7b-instruct-v0.3-q4_0

# Default target
.PHONY: all
all: start

# Start the entire stack (pull models, build, and run)
.PHONY: start
start: pull-models build up

# Pull required Ollama models
.PHONY: pull-models
pull-models:
	@echo "Starting Ollama service to pull models..."
	docker compose -f $(COMPOSE_FILE) up -d $(OLLAMA_SERVICE)
	@for model in $(MODELS); do \
		echo "Pulling model: $$model"; \
		docker compose -f $(COMPOSE_FILE) exec $(OLLAMA_SERVICE) ollama pull $$model; \
	done
	@echo "All models pulled successfully."

# Build Docker images
.PHONY: build
build:
	@echo "Building Docker images..."
	docker compose -f $(COMPOSE_FILE) build

# Start Docker Compose services
.PHONY: up
up:
	@echo "Starting Docker Compose services..."
	docker compose -f $(COMPOSE_FILE) up -d

# Stop and remove all services
.PHONY: down
down:
	@echo "Stopping and removing Docker Compose services..."
	docker compose -f $(COMPOSE_FILE) down

# Clean up volumes and images
.PHONY: clean
clean: down
	@echo "Removing Docker volumes and images..."
	docker volume rm $(shell docker volume ls -q | grep document-analysis-system) || true
	docker rmi $(shell docker images -q document-analysis-system_* -a) || true

# Check service status
.PHONY: status
status:
	@echo "Checking service status..."
	docker compose -f $(COMPOSE_FILE) ps
