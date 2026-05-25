from lib.config import config
from lib.ssh_lib.apt import apt_get_install
from lib.ssh_lib.utils import exists, put


def c1000k(c):
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


def wrk(c):
    apt_get_install(c, 'wrk')
    c.sudo('mkdir -p /data/ofm/benchmark')
    put(c, config.repo_root / 'docs' / 'benchmark' / 'wrk_custom_list.lua', '/data/ofm/benchmark')
