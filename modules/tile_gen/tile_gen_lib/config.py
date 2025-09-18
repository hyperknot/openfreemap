import subprocess
from pathlib import Path


class Configuration:
    areas = ['planet', 'monaco']

    tile_gen_dir = Path('/data/ofm/tile_gen')

    tile_gen_bin = tile_gen_dir / 'bin'
    tile_gen_scripts_dir = tile_gen_bin / 'scripts'

    planetiler_bin = tile_gen_dir / 'planetiler'
    planetiler_path = planetiler_bin / 'planetiler.jar'

    runs_dir = tile_gen_dir / 'runs'

    if Path('/data/ofm').exists():
        ofm_config_dir = Path('/data/ofm/config')
    else:
        repo_root = Path(__file__).parent.parent.parent.parent
        ofm_config_dir = repo_root / 'config'

    rclone_config = ofm_config_dir / 'rclone.conf'
    rclone_bin = subprocess.run(['which', 'rclone'], capture_output=True, text=True).stdout.strip()


config = Configuration()
