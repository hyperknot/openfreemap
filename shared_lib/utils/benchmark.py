from fabric import Connection

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from shared_lib.ssh_lib.apt import apt_get_install
from shared_lib.ssh_lib.utils import exists, put


def c1000k(c: Connection) -> None:
    if exists(c, 'c1000k-master'):
        return

    c.run('wget https://github.com/ideawu/c1000k/archive/master.zip -O tmp.zip')
    c.run('unzip -o tmp.zip')
    c.run('rm tmp.zip')
    c.run('cd c1000k-master && make')

    # usage
    # ./server 7000
    # ./client 127.0.0.1 7000
    # make sure it runs till 1 million


def wrk(c: Connection) -> None:
    apt_get_install(c, 'wrk')
    c.sudo('mkdir -p /data/ofm/benchmark')
    put(
        c,
        linux_host_deploy_config.local_repo_root / 'docs' / 'benchmark' / 'wrk_custom_list.lua',
        '/data/ofm/benchmark',
    )
