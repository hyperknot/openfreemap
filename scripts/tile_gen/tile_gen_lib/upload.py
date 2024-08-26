import subprocess

from tile_gen_lib.config import config


def upload_rclone(area, run):
    subprocess.run(
        [
            'rclone',
            'sync',
            '--transfers=8',
            '--multi-thread-streams=8',
            '--fast-list',
            '-v',
            '--stats-file-name-length',
            '0',
            '--stats-one-line',
            '--log-file',
            config.runs_dir / area / run / 'logs' / 'rclone.log',
            '--exclude',
            'logs/**',
            config.runs_dir / area / run,
            f'remote:ofm-{area}/{run}',
        ],
        env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
        check=True,
    )


def make_indexes():
    for area in config.areas:
        print(f'creating index {area}')

        # files
        p = subprocess.run(
            [
                'rclone',
                'lsf',
                '-R',
                '--files-only',
                '--fast-list',
                '--exclude',
                'dirs.txt',
                '--exclude',
                'index.txt',
                f'remote:ofm-{area}',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            capture_output=True,
            text=True,
        )
        index_str = p.stdout

        subprocess.run(
            [
                'rclone',
                'rcat',
                f'remote:ofm-{area}/index.txt',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            input=index_str.encode(),
        )

        # directories
        p = subprocess.run(
            [
                'rclone',
                'lsf',
                '-R',
                '--dirs-only',
                '--dir-slash=false',
                '--fast-list',
                f'remote:ofm-{area}',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            capture_output=True,
            text=True,
        )
        index_str = p.stdout

        subprocess.run(
            [
                'rclone',
                'rcat',
                f'remote:ofm-{area}/dirs.txt',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            input=index_str.encode(),
        )
