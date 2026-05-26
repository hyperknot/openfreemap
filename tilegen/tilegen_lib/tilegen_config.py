import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TilegenConfig:
    areas: tuple[str, ...] = ('planet', 'monaco')

    repo_root: Path = Path(__file__).resolve().parents[2]

    tilegen_dir: Path = Path('/data/ofm/tilegen')
    planetiler_bin: Path = tilegen_dir / 'planetiler'
    planetiler_path: Path = planetiler_bin / 'planetiler.jar'
    pmtiles_bin: Path = tilegen_dir / 'pmtiles'
    pmtiles_path: Path = pmtiles_bin / 'pmtiles'
    runs_dir: Path = tilegen_dir / 'runs'

    if Path('/data/ofm').exists():
        tilegen_config_dir: Path = Path('/data/ofm/config/tilegen')
    else:
        tilegen_config_dir: Path = repo_root / 'config' / 'tilegen'

    rclone_config: Path = tilegen_config_dir / 'rclone.conf'
    rclone_bin: str = subprocess.run(
        ['which', 'rclone'], capture_output=True, text=True
    ).stdout.strip()


tilegen_config = TilegenConfig()
