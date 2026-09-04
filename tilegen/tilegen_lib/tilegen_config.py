from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from shared_lib.utils.jsonc_config import read_jsonc_config


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

    telegram_token: str | None = field(init=False)
    telegram_chat_id: str | None = field(init=False)
    telegram_topic_id: int | None = field(init=False)

    rclone_config: Path = field(init=False)

    def __post_init__(self) -> None:
        if self.ofm_dir.exists():
            self.config_dir = self.ofm_dir / 'config'
        else:
            self.config_dir = self.repo_root / 'config'

        self.tilegen_config_dir = self.config_dir / 'tilegen'

        jsonc_path = self.tilegen_config_dir / 'config.jsonc'
        if not jsonc_path.is_file():
            raise FileNotFoundError(f'Tilegen config file not found: {jsonc_path}')

        jsonc_data = read_jsonc_config(jsonc_path)
        self.telegram_token = jsonc_data.get('telegram_token')
        self.telegram_chat_id = jsonc_data.get('telegram_chat_id')
        self.telegram_topic_id = jsonc_data.get('telegram_topic_id')
        self.rclone_config = self.tilegen_config_dir / 'rclone.conf'


@cache
def get_tilegen_config() -> TilegenConfig:
    # Resolve config lazily so CLI help and helper imports work without
    # ignored machine-specific files; each process still has one fixed config.
    # The accessor avoids threading config through every helper; command-local
    # imports would not decouple reusable helper imports from config.
    return TilegenConfig()
