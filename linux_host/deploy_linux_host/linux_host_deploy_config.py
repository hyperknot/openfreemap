import os
from pathlib import Path


class LinuxHostDeployConfig:
    repo_root = Path(__file__).resolve().parents[2]

    local_config_dir = repo_root / 'config'
    local_linux_host_config_dir = local_config_dir / 'linux_host'
    local_linux_host_dir = repo_root / 'linux_host'

    ENV = os.getenv('ENV')
    if not ENV:
        local_config_jsonc = local_linux_host_config_dir / 'config.jsonc'
    else:
        local_config_jsonc = local_linux_host_config_dir / f'{ENV}.jsonc'

    config_schema_json = local_linux_host_config_dir / 'schema.json'

    # Remote paths (always forward / on Linux - not using pathlib)
    ofm_dir = '/data/ofm'
    source_dir = f'{ofm_dir}/src'
    remote_config = f'{ofm_dir}/config'
    remote_linux_host_config = f'{remote_config}/linux_host'

    linux_host_dir = f'{ofm_dir}/linux_host'


linux_host_deploy_config = LinuxHostDeployConfig()
