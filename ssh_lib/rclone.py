from ssh_lib.utils import apt_get_update


def install_rclone(c):
    apt_get_update(c)
    c.sudo('curl https://rclone.org/install.sh | sudo bash')
