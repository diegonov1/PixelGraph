.PHONY: install dev dev-backend dev-frontend build clean test docker-dev docker-prod

# Install all dependencies
install:
	pip install -r requirements.txt
	cd frontend && npm install

# Run both backend and frontend for development
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@make -j2 dev-backend dev-frontend

# Run backend only
dev-backend:
	python examples/simple_demo.py

# Run frontend only
dev-frontend:
	cd frontend && npm run dev

# Build frontend and copy to pixelgraph/static
build:
	cd frontend && npm run build

# Clean build artifacts
clean:
	rm -rf pixelgraph/static/*
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run tests
test:
	pytest tests/ -v

# Docker development
docker-dev:
	docker-compose up backend frontend

# Docker production
docker-prod:
	docker-compose --profile prod up production

# Build production Docker image
docker-build:
	docker build -t pixelgraph:latest .

# Format code
format:
	black pixelgraph/ examples/ tests/
	cd frontend && npm run lint -- --fix

# Type check
typecheck:
	mypy pixelgraph/
