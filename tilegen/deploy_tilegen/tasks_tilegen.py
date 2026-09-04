import shlex
from pathlib import Path

from fabric import Connection

from shared_lib.ssh_lib.devops import ensure_rclone
from shared_lib.ssh_lib.utils import put
from shared_lib.utils.jsonc_config import read_jsonc_config
from tilegen.deploy_tilegen.install_planetiler import install_planetiler
from tilegen.deploy_tilegen.install_pmtiles import install_pmtiles
from tilegen.deploy_tilegen.tilegen_deploy_config import tilegen_deploy_config


TILE_BUILD_PATTERN = r'[t]ilegen/scripts/tilegen\.py make-tiles'
TILEGEN_PROCESS_PATTERN = r'[t]ilegen/scripts/tilegen\.py'


def tile_build_running(c: Connection) -> bool:
    return c.sudo(f'pgrep -f {shlex.quote(TILE_BUILD_PATTERN)}', warn=True, hide=True).ok


def disable_tilegen_cron(c: Connection) -> None:
    c.sudo('rm -f /etc/cron.d/ofm_tilegen')


def stop_tilegen(c: Connection) -> None:
    # Reinstall is explicitly destructive, so stop every tilegen command before
    # removing data. Child processes include Java, rclone, rsync, and mount helpers.
    for signal in ('TERM', 'KILL'):
        command = (
            f'for pid in $(pgrep -f {shlex.quote(TILEGEN_PROCESS_PATTERN)}); do '
            f'pkill -{signal} -P "$pid" || true; done'
        )
        c.sudo(f'bash -c {shlex.quote(command)}', warn=True)
        c.sudo(f'pkill -{signal} -f {shlex.quote(TILEGEN_PROCESS_PATTERN)}', warn=True)
        if signal == 'TERM':
            c.run('sleep 5')

    if c.sudo(f'pgrep -f {shlex.quote(TILEGEN_PROCESS_PATTERN)}', warn=True, hide=True).ok:
        raise RuntimeError('Tilegen processes are still running after SIGKILL')


def unmount_tilegen_filesystems(c: Connection) -> None:
    mounts = "findmnt -rn -o TARGET | grep '^/data/ofm/' | sort -r"
    c.sudo(f'bash -c {shlex.quote(f"{mounts} | xargs -r -n1 umount")}')
    if c.sudo("findmnt -rn -o TARGET | grep -q '^/data/ofm/'", warn=True, hide=True).ok:
        raise RuntimeError('Filesystems are still mounted below /data/ofm')


def prepare_tilegen(c: Connection, config_path: Path, *, enable_cron: bool) -> None:
    read_jsonc_config(config_path)

    ensure_rclone(c)
    install_planetiler(c)
    install_pmtiles(c)

    put(
        c,
        config_path,
        f'{tilegen_deploy_config.remote_tilegen_config}/config.jsonc',
        permissions='600',
        user='ofm',
        create_parent_dir=True,
    )
    put(
        c,
        tilegen_deploy_config.local_tilegen_config_dir / 'schema.json',
        f'{tilegen_deploy_config.remote_tilegen_config}/schema.json',
        user='ofm',
    )

    rclone_config = tilegen_deploy_config.local_tilegen_config_dir / 'rclone.conf'
    if rclone_config.exists():
        put(
            c,
            rclone_config,
            f'{tilegen_deploy_config.remote_tilegen_config}/rclone.conf',
            permissions='600',
            user='ofm',
        )

    c.sudo(f'mkdir -p {tilegen_deploy_config.remote_tilegen_dir}/logs')
    c.sudo(
        f'chown ofm:ofm {tilegen_deploy_config.remote_tilegen_dir} '
        + f'{tilegen_deploy_config.remote_tilegen_dir}/logs'
    )

    if enable_cron:
        put(c, tilegen_deploy_config.local_tilegen_dir / 'cron.d' / 'ofm_tilegen', '/etc/cron.d/')
