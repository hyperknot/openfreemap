import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class TilegenConfig:
    areas: tuple[str, ...] = ('planet', 'monaco')

    repo_root: Path = Path(__file__).resolve().parents[2]

    ofm_dir: Path = Path('/data/ofm')
    config_dir: Path = field(init=False)
    tilegen_config_dir: Path = field(init=False)
    tilegen_dir: Path = ofm_dir / 'tilegen'
    runs_dir: Path = tilegen_dir / 'runs'

    planetiler_bin_dir: Path = tilegen_dir / 'planetiler_bin'
    planetiler_path: Path = planetiler_bin_dir / 'planetiler.jar'
    pmtiles_bin_dir: Path = tilegen_dir / 'pmtiles_bin'
    pmtiles_path: Path = pmtiles_bin_dir / 'pmtiles'

    rclone_config: Path = field(init=False)
    rclone_bin: str = subprocess.run(
        ['which', 'rclone'], capture_output=True, text=True
    ).stdout.strip()

    def __post_init__(self) -> None:
        if self.ofm_dir.exists():
            self.config_dir = self.ofm_dir / 'config'
        else:
            self.config_dir = self.repo_root / 'config'

        self.tilegen_config_dir = self.config_dir / 'tilegen'
        self.rclone_config = self.tilegen_config_dir / 'rclone.conf'


tilegen_config = TilegenConfig()
