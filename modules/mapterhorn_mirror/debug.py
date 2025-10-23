#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#
# ]
# ///
import subprocess
from pathlib import Path
from urllib.parse import urlparse


rclone_config = Path('../../config/rclone.conf')

url = 'https://download.mapterhorn.com/planet.pmtiles'

# Parse URL properly
parsed = urlparse(url)
base_url = f'{parsed.scheme}://{parsed.netloc}'
path = parsed.path.lstrip('/')

destination = './downloads'

subprocess.run(
    [
        'rclone',
        'copy',
        '--http-url',
        base_url,
        f':http:{path}',
        destination,
        '--dump',
        'headers',
        '-vv',
        '--config',
        rclone_config,
    ]
)
