import os
from dataclasses import dataclass
from pathlib import Path


ENV = os.getenv('ENV')


@dataclass(slots=True)
class LinuxHostDeployConfig:
    local_repo_root: Path = Path(__file__).resolve().parents[2]

    local_config_dir: Path = local_repo_root / 'config'
    local_linux_host_config_dir: Path = local_config_dir / 'linux_host'
    local_linux_host_dir: Path = local_repo_root / 'linux_host'

    if not ENV:
        local_config_jsonc: Path = local_linux_host_config_dir / 'config.jsonc'
    else:
        local_config_jsonc: Path = local_linux_host_config_dir / f'{ENV}.jsonc'

    # Remote paths (always forward / on Linux - not using pathlib)
    remote_ofm_dir: str = '/data/ofm'
    remote_source_dir: str = f'{remote_ofm_dir}/src'
    remote_config_dir: str = f'{remote_ofm_dir}/config'
    remote_linux_host_config: str = f'{remote_config_dir}/linux_host'

    remote_linux_host_dir: str = f'{remote_ofm_dir}/linux_host'


linux_host_deploy_config = LinuxHostDeployConfig()
