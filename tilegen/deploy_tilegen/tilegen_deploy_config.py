from pathlib import Path


class TilegenDeployConfig:
    repo_root = Path(__file__).resolve().parents[2]

    local_config_dir = repo_root / 'config'
    local_tilegen_dir = repo_root / 'tilegen'

    # Remote paths (always forward / on Linux - not using pathlib)
    ofm_dir = '/data/ofm'
    source_dir = f'{ofm_dir}/src'
    remote_config = f'{ofm_dir}/config'
    remote_tilegen_config = f'{remote_config}/tilegen'

    tilegen_dir = f'{ofm_dir}/tilegen'
    planetiler_src = f'{tilegen_dir}/planetiler_src'
    planetiler_bin = f'{tilegen_dir}/planetiler'
    pmtiles_bin = f'{tilegen_dir}/pmtiles'


tilegen_deploy_config = TilegenDeployConfig()
