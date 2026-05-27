from fabric import Connection

from .apt import apt_get_update
from .utils import exists


def rclone(c: Connection) -> None:
    if exists(c, '/usr/bin/rclone'):
        return

    apt_get_update(c)
    c.sudo('curl https://rclone.org/install.sh | sudo bash')
