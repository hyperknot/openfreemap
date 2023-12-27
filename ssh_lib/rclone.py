from ssh_lib.utils import apt_get_update, exists


def install_rclone(c):
    if exists(c, '/usr/bin/rclone'):
        return

    apt_get_update(c)
    c.sudo('curl https://rclone.org/install.sh | sudo bash')
