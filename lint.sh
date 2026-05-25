#!/usr/bin/env bash
set -e

node_modules/.bin/prettier -w "**/*.md"

# biome
#pnpm biome check --write --unsafe --colors=off --log-level=info --log-kind=pretty . | grep path | sort
pnpm biome check --write --unsafe .

uv run ruff check --fix .
uv run ruff format .

find . -type f -name '*.conf' -path '*/nginx*' -exec uv run nginxfmt -v {} +;



