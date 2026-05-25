import subprocess
from pathlib import Path


class Configuration:
    areas = ['planet', 'monaco']

    repo_root = Path(__file__).resolve().parent.parent
    package_dir = Path(__file__).resolve().parent
    scripts_dir = package_dir / 'scripts'

    tilegen_dir = Path('/data/ofm/tilegen')
    planetiler_bin = tilegen_dir / 'planetiler'
    planetiler_path = planetiler_bin / 'planetiler.jar'
    runs_dir = tilegen_dir / 'runs'

    if Path('/data/ofm').exists():
        ofm_config_dir = Path('/data/ofm/config')
    else:
        ofm_config_dir = repo_root / 'config'

    rclone_config = ofm_config_dir / 'rclone.conf'
    rclone_bin = subprocess.run(['which', 'rclone'], capture_output=True, text=True).stdout.strip()


config = Configuration()
