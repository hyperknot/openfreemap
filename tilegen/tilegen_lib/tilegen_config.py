import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class TilegenConfig:
    areas: tuple[str, ...] = ('planet', 'monaco')

    repo_root: Path = Path(__file__).resolve().parents[2]

    tilegen_dir: Path = Path('/data/ofm/tilegen')
    planetiler_bin: Path = tilegen_dir / 'planetiler_bin'
    planetiler_path: Path = planetiler_bin / 'planetiler.jar'
    pmtiles_bin: Path = tilegen_dir / 'pmtiles_bin'
    pmtiles_path: Path = pmtiles_bin / 'pmtiles'
    runs_dir: Path = tilegen_dir / 'runs'

    tilegen_config_dir: Path = field(init=False)
    rclone_config: Path = field(init=False)
    rclone_bin: str = subprocess.run(
        ['which', 'rclone'], capture_output=True, text=True
    ).stdout.strip()

    def __post_init__(self) -> None:
        if Path('/data/ofm').exists():
            self.tilegen_config_dir = Path('/data/ofm/config/tilegen')
        else:
            self.tilegen_config_dir = self.repo_root / 'config' / 'tilegen'

        self.rclone_config = self.tilegen_config_dir / 'rclone.conf'


tilegen_config = TilegenConfig()
