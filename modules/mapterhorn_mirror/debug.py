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

parsed = urlparse(url)
base_url = f'{parsed.scheme}://{parsed.netloc}'
path = parsed.path.lstrip('/')

bucket_name = 'ofm-mapterhorn'
remote_name = 'remote'
destination = f'{remote_name}:{bucket_name}'

common_opts = [
    # '--verbose=10',
    # '--dump',
    # 'headers',
    '--progress',
    '--config',
    rclone_config,
]

subprocess.run(
    [
        'rclone',
        'copy',
        '--http-url',
        base_url,
        f':http:{path}',
        destination,
        '--multi-thread-streams=8',
        '--s3-chunk-size=100M',
        *common_opts,
    ]
)
