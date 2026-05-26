# OpenFreeMap agent notes

## Project shape

This is a single Python uv project plus the website frontend.

Python packages:

- `shared_lib/` — shared Python code.
  - `shared_lib/get_version_shared.py` — shared deployed/version helpers.
  - `shared_lib/deploy/` and `shared_lib/ssh_lib/` — deployment and SSH server setup helpers.
- `linux_host/` — runtime code for Linux tile hosts.
  - Script: `linux_host/scripts/linux-host.py`
  - Runtime library: `linux_host/lib/`
  - Cron file: `linux_host/cron.d/ofm_linux_host`
- `tilegen/` — runtime code for tile generation.
  - Script: `tilegen/scripts/tilegen.py`
  - Runtime library: `tilegen/lib/`
  - Cron file: `tilegen/cron.d/ofm_tilegen`
- Deploy/debug scripts:
  - `linux_host/deploy_linux_host.py`
  - `tilegen/deploy_tilegen.py`
  - `debug.py`

Frontend/site code lives in `website/` and uses pnpm.

## Python workflow

Use uv for all Python work.

Common commands:

```bash
uv sync

./linux_host/scripts/linux-host.py --help
./linux_host/deploy_linux_host.py --help

./tilegen/scripts/tilegen.py --help
./tilegen/deploy_tilegen.py --help
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

Remote runtime commands should use the executable uv-shebang scripts, for example:

```bash
cd /data/ofm/src && sudo env PYTHONUNBUFFERED=1 ./linux_host/scripts/linux-host.py sync
cd /data/ofm/src && sudo env PYTHONUNBUFFERED=1 ./tilegen/scripts/tilegen.py make-tiles planet
```

## Code style

- Prefer simple, direct code over abstractions.

- Keep shared code in `shared_lib/`; do not duplicate helpers across `linux_host` and `tilegen`.
- Keep runtime package config local to each runtime package:
  - `linux_host/lib/linux_host_config.py` reads `config/linux_host` locally and `/data/ofm/config/linux_host` remotely
  - `tilegen/lib/tilegen_config.py` reads `config/tilegen` locally and `/data/ofm/config/tilegen` remotely
  - deployment config and deployment helpers live in each package's `deploy_lib/`:
    - `linux_host/deploy_lib/`
    - `tilegen/deploy_lib/`
  - shared deployment helpers stay in `shared_lib/deploy/`.
- Use Click for CLIs.
- Use ./lint.sh for linting and formatting.
