from pathlib import Path


class TilegenDeployConfig:
    repo_root = Path(__file__).resolve().parents[2]

    local_config_dir = repo_root / 'config'
    local_tilegen_dir = repo_root / 'tilegen'

    # Remote paths (always forward / on Linux - not using pathlib)
    remote_ofm_dir = '/data/ofm'
    remote_source_dir = f'{remote_ofm_dir}/src'
    remote_config_dir = f'{remote_ofm_dir}/config'
    remote_tilegen_config = f'{remote_config_dir}/tilegen'

    remote_tilegen_bin = f'{remote_ofm_dir}/tilegen'
    remote_planetiler_src = f'{remote_tilegen_bin}/planetiler_src'
    remote_planetiler_bin = f'{remote_tilegen_bin}/planetiler'
    remote_pmtiles_bin = f'{remote_tilegen_bin}/pmtiles'


tilegen_deploy_config = TilegenDeployConfig()
