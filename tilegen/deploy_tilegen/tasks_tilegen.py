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


def tile_build_running(c: Connection) -> bool:
    return c.sudo(f'pgrep -f {shlex.quote(TILE_BUILD_PATTERN)}', warn=True, hide=True).ok


def disable_tilegen_cron(c: Connection) -> None:
    c.sudo('rm -f /etc/cron.d/ofm_tilegen')


def stop_tilegen(c: Connection) -> None:
    # Reinstall is explicitly destructive, so stop every process working under
    # /data/ofm before removing it. Processes are selected by cwd, not by parent:
    # tilegen commands run from /data/ofm/src and their children (Java, rclone,
    # mount helpers) inherit a cwd below /data/ofm. This also catches orphans, e.g.
    # Java that ignored SIGTERM after its Python parent exited, even if the
    # directory was already deleted (cwd then reads '<path> (deleted)').
    ofm_dir = tilegen_deploy_config.remote_ofm_dir
    script = f"""
list_pids() {{
  for d in /proc/[0-9]*; do
    case "$(readlink "$d/cwd" 2>/dev/null)" in
      {ofm_dir}|{ofm_dir}/*) echo "${{d#/proc/}}" ;;
    esac
  done
}}

wait_gone() {{
  for _ in $(seq "$1"); do
    [ -z "$(list_pids)" ] && return 0
    sleep 1
  done
  return 1
}}

pids=$(list_pids)
[ -z "$pids" ] && exit 0
ps -o pid,user,args -p "$(echo $pids | tr ' ' ,)" | cut -c1-150

kill -TERM $pids 2>/dev/null
wait_gone 30 && exit 0

echo 'Processes still running after SIGTERM, sending SIGKILL'
kill -KILL $(list_pids) 2>/dev/null
wait_gone 60 && exit 0

echo 'Processes still running after SIGKILL:'
ps -o pid,user,args -p "$(list_pids | paste -sd,)"
exit 1
"""
    c.sudo(f'bash -c {shlex.quote(script)}')


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

    # /data is owned by root, so deploy creates the persistent Wikidata cache dir for ofm.
    c.sudo('mkdir -p /data/ofm_keep/wikidata')
    c.sudo('chown -R ofm:ofm /data/ofm_keep')

    c.sudo(f'mkdir -p {tilegen_deploy_config.remote_tilegen_dir}/logs')
    c.sudo(
        f'chown ofm:ofm {tilegen_deploy_config.remote_tilegen_dir} '
        + f'{tilegen_deploy_config.remote_tilegen_dir}/logs'
    )

    if enable_cron:
        put(c, tilegen_deploy_config.local_tilegen_dir / 'cron.d' / 'ofm_tilegen', '/etc/cron.d/')
