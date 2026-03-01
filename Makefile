################################################################################################
# Makefile
################################################################################################

#-----------------------------------------------------------------------------------------------
# Shell variables
#-----------------------------------------------------------------------------------------------
# Console text colors :)
BOLD=$(shell tput bold)
RED=$(shell tput setaf 1)
GREEN=$(shell tput setaf 2)
YELLOW=$(shell tput setaf 3)
RESET=$(shell tput sgr0)

# Virtual environment
VENV_DIR = venv
VENV_PYTHON = $(VENV_DIR)/bin/python3
VENV_PIP = $(VENV_DIR)/bin/pip3
VENV_PRE_COMMIT = $(VENV_DIR)/bin/pre-commit
VENV_MY_PY = $(VENV_DIR)/bin/mypy

# Local
LOCAL_PYTHON = python3

#-----------------------------------------------------------------------------------------------
# Tasks
#-----------------------------------------------------------------------------------------------
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

#-----------------------------------------------------------------------------------------------
# Local
#-----------------------------------------------------------------------------------------------
.PHONY: local-bootstrap
local-bootstrap:  ## Bootstrap the local virtual environment (e.g. create virtualenv)
	@$(LOCAL_PYTHON) -m venv $(VENV_DIR)
	@# Needed because "source" is a shell built-in command and cannot be directly used in a Makefile.
	@echo "$(BOLD)$(YELLOW) To enable the environment on your shell, run the command: source $(VENV_DIR)/bin/activate"

.PHONY: local-init
local-init:  ## Init the local virtual environment (assumes virtualenv is enabled)
	@$(VENV_PIP) install -r requirements-local.txt
	@$(VENV_PRE_COMMIT) install

.PHONY: local-lint
local-lint:   ## Apply linting
	@$(VENV_PRE_COMMIT) run --all-files
	@$(VENV_MY_PY) .

.PHONY: local-clean
local-clean:  ## Clean the local environment
	@rm -rf $(VENV_DIR)
	@# Needed because "source" is a shell built-in command and cannot be directly used in a Makefile.
	@echo "$(BOLD)$(YELLOW) To disable the environment on your shell, run the command: deactivate"

#-----------------------------------------------------------------------------------------------
# Docker compose
#-----------------------------------------------------------------------------------------------
.PHONY: compose-build
compose-build:  ## Build Docker compose images
	@docker-compose -f .docker-compose/docker-compose.yaml build --build-arg ENV_REQ=requirements-local.txt

.PHONY: compose-run
compose-run:  ## Run Docker compose services
	@docker-compose -f .docker-compose/docker-compose.yaml up -d

.PHONY: compose-test
compose-test:  ## Run tests
	@docker-compose -f .docker-compose/docker-compose.yaml run api pytest -vv

# Default command to help
.DEFAULT_GOAL := help
