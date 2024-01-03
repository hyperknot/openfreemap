import subprocess
from pathlib import Path

from http_host_lib import DEFAULT_RUNS_DIR, MNT_DIR


def clean_up_mounts(mnt_dir):
    if not mnt_dir.exists():
        return

    print('Cleaning up mounts')

    # handle deleted files
    p = subprocess.run(['mount'], capture_output=True, text=True, check=True)
    lines = [l for l in p.stdout.splitlines() if f'{mnt_dir}/' in l and '(deleted)' in l]

    for l in lines:
        mnt_path = Path(l.split('(deleted) on ')[1].split(' type btrfs')[0])
        print(f'  removing deleted mount {mnt_path}')
        assert mnt_path.exists()
        subprocess.run(['umount', mnt_path], check=True)
        mnt_path.rmdir()

    # clean all mounts not in current fstab
    with open('/etc/fstab') as fp:
        fstab_str = fp.read()

    for subdir in mnt_dir.iterdir():
        if f'{subdir} ' in fstab_str:
            continue

        print(f'  removing old mount {subdir}')
        subprocess.run(['umount', subdir], check=True)
        subdir.rmdir()


def create_fstab():
    fstab_new = []

    for area in ['planet', 'monaco']:
        area_dir = (DEFAULT_RUNS_DIR / area).resolve()
        if not area_dir.exists():
            continue

        versions = sorted(area_dir.iterdir())
        for version in versions:
            version_str = version.name
            btrfs_file = area_dir / version_str / 'tiles.btrfs'
            if not btrfs_file.is_file():
                continue

            mnt_folder = MNT_DIR / f'{area}-{version_str}'
            mnt_folder.mkdir(exist_ok=True, parents=True)

            fstab_new.append(f'{btrfs_file} {mnt_folder} btrfs loop,ro 0 0\n')
            print(f'Created fstab entry for {btrfs_file} -> {mnt_folder}')

    with open('/etc/fstab') as fp:
        fstab_orig = [l for l in fp.readlines() if f'{MNT_DIR}/' not in l]

    with open('/etc/fstab', 'w') as fp:
        fp.writelines(fstab_orig + fstab_new)
