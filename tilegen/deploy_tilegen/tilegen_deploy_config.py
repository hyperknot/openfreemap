from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TilegenDeployConfig:
    local_repo_root: Path = Path(__file__).resolve().parents[2]
    local_config_dir: Path = local_repo_root / 'config'
    local_tilegen_dir: Path = local_repo_root / 'tilegen'

    # Remote paths (always forward / on Linux - not using pathlib)
    remote_ofm_dir: str = '/data/ofm'
    remote_source_dir: str = f'{remote_ofm_dir}/src'
    remote_config_dir: str = f'{remote_ofm_dir}/config'
    remote_tilegen_config: str = f'{remote_config_dir}/tilegen'

    remote_tilegen_bin: str = f'{remote_ofm_dir}/tilegen'
    remote_planetiler_src: str = f'{remote_tilegen_bin}/planetiler_src'
    remote_planetiler_bin: str = f'{remote_tilegen_bin}/planetiler_bin'
    remote_pmtiles_bin: str = f'{remote_tilegen_bin}/pmtiles_bin'


tilegen_deploy_config = TilegenDeployConfig()
