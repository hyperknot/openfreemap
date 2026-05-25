#!/usr/bin/env bash
set -euxo pipefail

if ! command -v hk >/dev/null 2>&1; then
  brew install hk
fi
hk install


hk fix --all

#pnpm typecheck
#pnpm --dir website typecheck
