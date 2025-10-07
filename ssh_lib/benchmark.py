from ssh_lib.config import config
from ssh_lib.utils import apt_get_install, exists, put


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
    put(c, f'{config.modules_dir}/http_host/benchmark/wrk_custom_list.lua', '/data/ofm/benchmark')
