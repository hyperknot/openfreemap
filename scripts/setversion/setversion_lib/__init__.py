from pathlib import Path


if Path('/data/ofm/config').exists():
    OFM_CONFIG_DIR = Path('/data/ofm/config')
else:
    OFM_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / 'config'

assert OFM_CONFIG_DIR.exists()

RCLONE_CONF = OFM_CONFIG_DIR / 'rclone.conf'

if Path('/opt/homebrew/bin/rclone').exists():
    RCLONE_BIN = '/opt/homebrew/bin/rclone'
else:
    RCLONE_BIN = 'rclone'
