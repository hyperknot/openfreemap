from pathlib import Path


if Path('/data/ofm/config').exists():
    OFM_CONFIG_DIR = Path('/data/ofm/config')
else:
    OFM_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / 'config'

assert OFM_CONFIG_DIR.exists()
