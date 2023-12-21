from ssh_lib.config import scripts
from ssh_lib.utils import apt_get_install, apt_get_update, put, put_str, sudo_cmd


def c1000k(c):
    c.run('wget https://github.com/ideawu/c1000k/archive/master.zip -O tmp.zip')
    c.run('unzip -o tmp.zip')
    c.run('rm tmp.zip')
    c.run('cd c1000k-master && make')

    # usage
    # ./server 7000
    # ./client 127.0.0.1 7000
    # make sure it runs till 1 million


def benchmark(c):
    apt_get_install(c, 'wrk')
    c.sudo('mkdir -p /data/ofm/benchmark')
    put(c, f'{scripts}/benchmark/wrk_custom_list.lua', '/data/ofm/benchmark')

    # wrk -c10 -d10s -t1 -s /data/ofm/benchmark/wrk_custom_list.lua http://localhost
