import subprocess
from pathlib import Path


class Configuration:
    areas = ['planet', 'monaco']

    repo_root = Path(__file__).resolve().parents[2]

    tilegen_dir = Path('/data/ofm/tilegen')
    planetiler_bin = tilegen_dir / 'planetiler'
    planetiler_path = planetiler_bin / 'planetiler.jar'
    runs_dir = tilegen_dir / 'runs'

    if Path('/data/ofm').exists():
        tilegen_config_dir = Path('/data/ofm/config/tilegen')
    else:
        tilegen_config_dir = repo_root / 'config' / 'tilegen'

    rclone_config = tilegen_config_dir / 'rclone.conf'
    rclone_bin = subprocess.run(['which', 'rclone'], capture_output=True, text=True).stdout.strip()


config = Configuration()
