.PHONY: help install install-backend install-frontend setup-env run run-backend run-frontend run-fullstack build clean test lint format

# Variables
VENV = stockbot_env
VENV_BIN = $(VENV)/bin
PYTHON = $(VENV_BIN)/python
PIP = $(VENV_BIN)/pip
BACKEND_DIR = backend
FRONTEND_DIR = react-frontend
PORT_BACKEND = 8001
PORT_FRONTEND = 5173

# Colors for output
CYAN = \033[0;36m
GREEN = \033[0;32m
YELLOW = \033[0;33m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Stock-Bot Makefile Commands:$(NC)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install all dependencies (backend + frontend)

install-backend: ## Install Python backend dependencies
	@echo "$(CYAN)Installing backend dependencies...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		python3 -m venv $(VENV); \
	fi
	@echo "$(CYAN)Activating virtual environment and installing packages...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## Install frontend dependencies
	@echo "$(CYAN)Installing frontend dependencies...$(NC)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

setup-env: ## Create .env files from examples (if they don't exist)
	@echo "$(CYAN)Setting up environment files...$(NC)"
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env 2>/dev/null || echo "$(YELLOW)⚠ $(BACKEND_DIR)/.env.example not found. Please create $(BACKEND_DIR)/.env manually$(NC)"; \
		echo "$(GREEN)✓ Created $(BACKEND_DIR)/.env$(NC)"; \
	else \
		echo "$(YELLOW)⚠ $(BACKEND_DIR)/.env already exists$(NC)"; \
	fi
	@if [ ! -f $(FRONTEND_DIR)/.env ]; then \
		cp $(FRONTEND_DIR)/.env.example $(FRONTEND_DIR)/.env 2>/dev/null || echo "$(YELLOW)⚠ $(FRONTEND_DIR)/.env.example not found$(NC)"; \
		echo "$(GREEN)✓ Created $(FRONTEND_DIR)/.env$(NC)"; \
	else \
		echo "$(YELLOW)⚠ $(FRONTEND_DIR)/.env already exists$(NC)"; \
	fi
	@echo "$(CYAN)Don't forget to add your API keys to $(BACKEND_DIR)/.env!$(NC)"

run: run-fullstack ## Run both backend and frontend (default)

run-backend: ## Run backend server only
	@echo "$(CYAN)Starting backend server on port $(PORT_BACKEND)...$(NC)"
	@cd $(BACKEND_DIR) && $(VENV_BIN)/uvicorn main:app --reload --host 0.0.0.0 --port $(PORT_BACKEND)

run-frontend: ## Run frontend dev server only
	@echo "$(CYAN)Starting frontend dev server on port $(PORT_FRONTEND)...$(NC)"
	@cd $(FRONTEND_DIR) && npm run dev

run-fullstack: ## Run both backend and frontend together
	@echo "$(CYAN)Starting full-stack application...$(NC)"
	@cd $(FRONTEND_DIR) && npm run dev:fullstack

build: build-frontend ## Build frontend for production

build-frontend: ## Build frontend for production
	@echo "$(CYAN)Building frontend for production...$(NC)"
	@cd $(FRONTEND_DIR) && npm run build
	@echo "$(GREEN)✓ Frontend built successfully$(NC)"

run-prod: ## Run production build (backend serves frontend)
	@echo "$(CYAN)Starting production server...$(NC)"
	@cd $(FRONTEND_DIR) && npm run start:prod

clean: clean-python clean-node clean-build ## Clean all generated files

clean-python: ## Clean Python cache files
	@echo "$(CYAN)Cleaning Python cache files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Python cache cleaned$(NC)"

clean-node: ## Clean node_modules and build files
	@echo "$(CYAN)Cleaning node_modules and build files...$(NC)"
	@cd $(FRONTEND_DIR) && rm -rf node_modules dist .vite 2>/dev/null || true
	@echo "$(GREEN)✓ Node files cleaned$(NC)"

clean-build: ## Clean build directories
	@echo "$(CYAN)Cleaning build directories...$(NC)"
	@rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/build 2>/dev/null || true
	@echo "$(GREEN)✓ Build directories cleaned$(NC)"

clean-venv: ## Remove virtual environment
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	@rm -rf $(VENV)
	@echo "$(GREEN)✓ Virtual environment removed$(NC)"

test: ## Run tests (placeholder - add your test commands)
	@echo "$(CYAN)Running tests...$(NC)"
	@echo "$(YELLOW)⚠ No tests configured yet$(NC)"

lint: lint-backend lint-frontend ## Lint backend and frontend code

lint-backend: ## Lint Python code
	@echo "$(CYAN)Linting backend code...$(NC)"
	@echo "$(YELLOW)⚠ Add flake8, black, or pylint to lint Python code$(NC)"

lint-frontend: ## Lint frontend code
	@echo "$(CYAN)Linting frontend code...$(NC)"
	@cd $(FRONTEND_DIR) && npm run lint 2>/dev/null || echo "$(YELLOW)⚠ No lint script found in package.json$(NC)"

format: format-backend format-frontend ## Format backend and frontend code

format-backend: ## Format Python code
	@echo "$(CYAN)Formatting backend code...$(NC)"
	@echo "$(YELLOW)⚠ Add black or autopep8 to format Python code$(NC)"

format-frontend: ## Format frontend code
	@echo "$(CYAN)Formatting frontend code...$(NC)"
	@cd $(FRONTEND_DIR) && npm run format 2>/dev/null || echo "$(YELLOW)⚠ No format script found in package.json$(NC)"

check-env: ## Check if required environment files exist
	@echo "$(CYAN)Checking environment setup...$(NC)"
	@if [ -f $(BACKEND_DIR)/.env ]; then \
		echo "$(GREEN)✓ $(BACKEND_DIR)/.env exists$(NC)"; \
	else \
		echo "$(YELLOW)✗ $(BACKEND_DIR)/.env missing - run 'make setup-env'$(NC)"; \
	fi
	@if [ -f $(BACKEND_DIR)/firebase-key.json ]; then \
		echo "$(GREEN)✓ $(BACKEND_DIR)/firebase-key.json exists$(NC)"; \
	else \
		echo "$(YELLOW)✗ $(BACKEND_DIR)/firebase-key.json missing - download from Firebase Console$(NC)"; \
	fi
	@if [ -d $(VENV) ]; then \
		echo "$(GREEN)✓ Virtual environment exists$(NC)"; \
	else \
		echo "$(YELLOW)✗ Virtual environment missing - run 'make install-backend'$(NC)"; \
	fi
	@if [ -d $(FRONTEND_DIR)/node_modules ]; then \
		echo "$(GREEN)✓ Frontend dependencies installed$(NC)"; \
	else \
		echo "$(YELLOW)✗ Frontend dependencies missing - run 'make install-frontend'$(NC)"; \
	fi

update-deps: ## Update all dependencies
	@echo "$(CYAN)Updating dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install --upgrade -r requirements.txt
	@cd $(FRONTEND_DIR) && npm update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

info: ## Show project information
	@echo "$(CYAN)Stock-Bot Project Information:$(NC)"
	@echo ""
	@echo "$(GREEN)Backend:$(NC)"
	@echo "  Port: $(PORT_BACKEND)"
	@echo "  Virtual Env: $(VENV)"
	@echo "  Python: $$($(PYTHON) --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "$(GREEN)Frontend:$(NC)"
	@echo "  Port: $(PORT_FRONTEND)"
	@echo "  Node: $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "  NPM: $$(npm --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "$(GREEN)URLs:$(NC)"
	@echo "  Frontend: http://localhost:$(PORT_FRONTEND)"
	@echo "  Backend API: http://localhost:$(PORT_BACKEND)"
	@echo "  API Docs: http://localhost:$(PORT_BACKEND)/docs"
