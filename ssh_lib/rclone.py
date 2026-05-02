from ssh_lib.apt import apt_get_update
from ssh_lib.utils import exists


def rclone(c):
    if exists(c, '/usr/bin/rclone'):
        return

    apt_get_update(c)
    c.sudo('curl https://rclone.org/install.sh | sudo bash')
