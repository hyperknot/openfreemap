#!/usr/bin/env bash
set -euxo pipefail

find . -type d -name __pycache__ -prune -exec rm -rf {} +

if ! command -v hk >/dev/null 2>&1; then
  brew install hk
fi
hk install

hk fix --all

echo basedpyright
uv run basedpyright

#pnpm typecheck
#pnpm --dir website typecheck
