#!/usr/bin/env bash

find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
find . -name '*.pyc' -delete
find . -name .DS_Store -delete
find . -name .ipynb_checkpoints -exec rm -rf {} +
find . -name .mypy_cache -type d -prune -exec rm -rf {} +
find . -name .pnpm-store -exec rm -rf {} +
find . -name .pytest_cache -exec rm -rf {} +
find . -name .ruff_cache -exec rm -rf {} +
find . -name .venv -type d -prune -exec rm -rf {} +
find . -name __pycache__ -type d -prune -exec rm -rf {} +
find . -name node_modules -type d -prune -exec rm -rf {} +
find . -name venv -type d -prune -exec rm -rf {} +



# uv
uv sync

pnpm i --verbose
