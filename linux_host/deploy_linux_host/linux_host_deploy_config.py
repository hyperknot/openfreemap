import os
from pathlib import Path


ENV = os.getenv('ENV')


class LinuxHostDeployConfig:
    local_repo_root = Path(__file__).resolve().parents[2]

    local_config_dir = local_repo_root / 'config'
    local_linux_host_config_dir = local_config_dir / 'linux_host'
    local_linux_host_dir = local_repo_root / 'linux_host'

    if not ENV:
        local_config_jsonc = local_linux_host_config_dir / 'config.jsonc'
    else:
        local_config_jsonc = local_linux_host_config_dir / f'{ENV}.jsonc'

    # Remote paths (always forward / on Linux - not using pathlib)
    remote_ofm_dir = '/data/ofm'
    remote_source_dir = f'{remote_ofm_dir}/src'
    remote_config_dir = f'{remote_ofm_dir}/config'
    remote_linux_host_config = f'{remote_config_dir}/linux_host'

    remote_linux_host_dir = f'{remote_ofm_dir}/linux_host'


linux_host_deploy_config = LinuxHostDeployConfig()
