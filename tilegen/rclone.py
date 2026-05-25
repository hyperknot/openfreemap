import subprocess

from .config import config


# Files that are uploaded individually before finalize_run_upload
LARGE_FILES = {'tiles.mbtiles', 'tiles.btrfs', 'tiles.btrfs.gz'}


def finalize_run_upload(run_dir, remote_dir):
    """Upload remaining small files, SHA256SUMS last, then mark done."""
    for file in sorted(run_dir.iterdir()):
        if file.is_file() and file.name not in LARGE_FILES | {'SHA256SUMS', 'done'}:
            upload_run_file(file, remote_dir)

    upload_run_file(run_dir / 'SHA256SUMS', remote_dir)

    # create "done" file
    subprocess.run(
        ['rclone', 'touch', f'{remote_dir}/done'],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
    )


def upload_run_file(file, remote_dir):
    print(f'Uploading {file} to {remote_dir}')

    subprocess.run(
        [
            'rclone',
            'copyto',
            '--verbose=1',
            '--multi-thread-streams=8',
            '--stats-file-name-length=0',
            '--stats-one-line',
            str(file),
            f'{remote_dir}/{file.name}',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
    )


def make_indexes_for_bucket(bucket):
    print(f'Making indexes for bucket: {bucket}')

    # files
    p = subprocess.run(
        [
            'rclone',
            'lsf',
            '--recursive',
            '--files-only',
            '--fast-list',
            '--exclude',
            'dirs.txt',
            '--exclude',
            'files.txt',
            f'remote:{bucket}',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
        capture_output=True,
        text=True,
    )
    index_str = p.stdout

    # upload to files.txt
    subprocess.run(
        [
            'rclone',
            'rcat',
            f'remote:{bucket}/files.txt',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
        input=index_str.encode(),
    )

    # directories
    p = subprocess.run(
        [
            'rclone',
            'lsf',
            '--recursive',
            '--dirs-only',
            '--dir-slash=false',
            '--fast-list',
            f'remote:{bucket}',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
        capture_output=True,
        text=True,
    )
    index_str = p.stdout

    # upload to dirs.txt
    subprocess.run(
        [
            'rclone',
            'rcat',
            f'remote:{bucket}/dirs.txt',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
        input=index_str.encode(),
    )


def set_version_on_bucket(area, version):
    print(f'setting version: {area} {version}')
    subprocess.run(
        [
            config.rclone_bin,
            'rcat',
            f'remote:ofm-assets/deployed_versions/{area}.txt',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
        input=version.strip().encode(),
    )
