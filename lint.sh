#!/usr/bin/env bash

# biome
#pnpm biome check --write --unsafe --colors=off --log-level=info --log-kind=pretty . | grep path | sort
pnpm biome check --write --unsafe .

ruff check --fix .
ruff format .

find . -type f -name '*.conf' -path '*/nginx*' -exec nginxfmt -v {} +;



