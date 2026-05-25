# OpenFreeMap agent notes

## Project shape

This is a single Python uv project plus the website frontend.

Python packages:

- `lib/` — shared Python code.
  - `lib/get_version_shared.py` — shared deployed/version helpers.
  - `lib/ssh_lib/` — SSH deployment and server setup helpers.
- `linux_host/` — runtime code for Linux tile hosts.
  - CLI module: `linux_host.linux_host`
  - Installed command: `linux-host`
  - Cron file: `linux_host/cron.d/ofm_linux_host`
- `tilegen/` — runtime code for tile generation.
  - CLI module: `tilegen.tilegen`
  - Installed command: `tilegen`
  - Cron file: `tilegen/cron.d/ofm_tilegen`
- Root deploy scripts:
  - `deploy_linux_host.py`
  - `deploy_tilegen.py`
  - `debug.py`

Frontend/site code lives in `website/` and uses pnpm.

## Python workflow

Use uv for all Python work.

Common commands:

```bash
uv sync
uv run ruff check .
uv run ruff format .
uv run linux-host --help
uv run tilegen --help
uv run ./deploy_linux_host.py --help
uv run ./deploy_tilegen.py --help
uv build --wheel
```

Packaging is defined in `pyproject.toml` and uses `uv_build`. Keep it that way.

Runtime dependencies belong in `[project].dependencies`; local development tools belong in `[dependency-groups].dev`.

## Deployment model

Deployment uploads the full source tree to the server and syncs a uv environment there.

Remote layout:

- `/data/ofm/src` — uploaded source tree and uv project root.
- `/data/ofm/config/linux_host` — selected Linux host runtime config.
- `/data/ofm/config/tilegen` — selected tilegen runtime config.
- `/data/ofm/linux_host` — Linux host runtime data, logs, assets and runs.
- `/data/ofm/tilegen` — tile generation runtime data, logs, runs and Planetiler.

Do not implement partial-package or multi-repo deployment logic. Keep deployment simple: upload full source, then run uv from `/data/ofm/src`.

Remote runtime commands should use `uv run`, for example:

```bash
cd /data/ofm/src && sudo uv run python -u -m linux_host.linux_host sync
cd /data/ofm/src && sudo uv run python -u -m tilegen.tilegen make-tiles planet
```

## Code style

- Prefer simple, direct code over abstractions.
- Use absolute imports from `lib`, `linux_host`, and `tilegen`.
- Keep shared code in `lib/`; do not duplicate helpers across `linux_host` and `tilegen`.
- Keep runtime package config local to each runtime package:
  - `linux_host/config.py` reads `config/linux_host` locally and `/data/ofm/config/linux_host` remotely
  - `tilegen/config.py` reads `config/tilegen` locally and `/data/ofm/config/tilegen` remotely
  - deployment config in `lib/ssh_lib/config.py`
- Keep root deploy CLIs as real scripts with their logic in the script.
- Use Click for CLIs.
- Run `uv run ruff check .` after Python edits.

## Frontend workflow

Use pnpm for website work:

```bash
cd website
pnpm install
pnpm run build
```

## Generated files

Do not commit generated caches/build outputs such as:

- `dist/`
- `__pycache__/`
- `*.egg-info/`
- `.ruff_cache/`
- `node_modules/`
