import os
from pathlib import Path


class Configuration:
    # Local paths relative to this file
    assets_dir = Path(__file__).parent / 'assets'
    config_dir = Path(__file__).parent.parent / 'config'
    modules_dir = Path(__file__).parent.parent / 'modules'

    ENV = os.getenv('ENV')
    if not ENV:
        config_jsonc = config_dir / 'config.jsonc'
    else:
        config_jsonc = config_dir / f'config.{ENV}.jsonc'

    # remote paths (always Linux /, not using pathlib)
    ofm_dir = '/data/ofm'
    remote_config = f'{ofm_dir}/config'
    venv_bin = f'{ofm_dir}/venv/bin'

    # remote http_host dir
    http_host_dir = f'{ofm_dir}/http_host'
    http_host_bin = f'{http_host_dir}/bin'

    # remote tile_gen_dir
    tile_gen_dir = f'{ofm_dir}/tile_gen'
    tile_gen_bin = f'{tile_gen_dir}/bin'
    planetiler_src = f'{tile_gen_dir}/planetiler_src'
    planetiler_bin = f'{tile_gen_dir}/planetiler'


config = Configuration()
