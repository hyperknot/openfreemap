import shutil
import subprocess
import sys
from pathlib import Path

from http_host_lib import (
    CERTS_DIR,
    DEFAULT_RUNS_DIR,
    HOST_CONFIG,
    HTTP_HOST_BIN_DIR,
    MNT_DIR,
    NGINX_DIR,
    OFM_CONFIG_DIR,
)


def write_nginx_config():
    curl_text_mix = ''

    domain_le = HOST_CONFIG['domain_le']
    domain_ledns = HOST_CONFIG['domain_ledns']

    # remove old configs and certs
    for file in Path('/data/nginx/sites').glob('ofm_*.conf'):
        file.unlink()

    for file in Path('/data/nginx/certs').glob('ofm_*'):
        file.unlink()

    # processing Round Robin DNS config
    if domain_ledns:
        if not (OFM_CONFIG_DIR / 'rclone.conf').is_file():
            sys.exit('rclone.conf missing')

        # download the ledns certificate from bucket using rclone
        write_ledns_reader_script(domain_ledns)
        subprocess.run(['bash', HTTP_HOST_BIN_DIR / 'ledns_reader.sh'], check=True)

        curl_text_mix += create_nginx_conf(
            template_path=NGINX_DIR / 'ledns.conf',
            local='ofm_ledns',
            domain=domain_ledns,
        )

    # processing Let's Encrypt config
    if domain_le:
        le_cert = CERTS_DIR / 'ofm_le.cert'
        le_key = CERTS_DIR / 'ofm_le.key'

        if not le_cert.is_file() or not le_key.is_file():
            shutil.copyfile(Path('/etc/nginx/ssl/dummy.crt'), le_cert)
            shutil.copyfile(Path('/etc/nginx/ssl/dummy.key'), le_key)

        curl_text_mix += create_nginx_conf(
            template_path=NGINX_DIR / 'le.conf',
            local='ofm_le',
            domain=domain_le,
        )

        subprocess.run(['nginx', '-t'], check=True)
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)

        subprocess.run(
            [
                'certbot',
                'certonly',
                '--webroot',
                '--webroot-path=/data/nginx/acme-challenges',
                '--noninteractive',
                '-m',
                HOST_CONFIG['le_email'],
                '--agree-tos',
                '--cert-name=ofm_le',
                # '--staging',
                '--deploy-hook',
                'nginx -t && service nginx reload',
                '-d',
                domain_le,
            ],
            check=True,
        )

        # link certs to nginx dir
        le_cert.unlink()
        le_key.unlink()

        etc_cert = Path('/etc/letsencrypt/live/ofm_le/fullchain.pem')
        etc_key = Path('/etc/letsencrypt/live/ofm_le/privkey.pem')
        assert etc_cert.is_file()
        assert etc_key.is_file()
        le_cert.symlink_to(etc_cert)
        le_key.symlink_to(etc_key)

    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=True)

    print(curl_text_mix)


def create_nginx_conf(*, template_path, local, domain):
    location_str, curl_text = create_location_blocks(local=local, domain=domain)

    with open(template_path) as fp:
        template = fp.read()

    template = template.replace('__LOCATION_BLOCKS__', location_str)
    template = template.replace('__LOCAL__', local)
    template = template.replace('__DOMAIN__', domain)

    curl_text = curl_text.replace('__LOCAL__', local)
    curl_text = curl_text.replace('__DOMAIN__', domain)

    with open(f'/data/nginx/sites/{local}.conf', 'w') as fp:
        fp.write(template)
        print(f'  nginx config written: {domain} {local}')

    return curl_text


def create_location_blocks(*, local, domain):
    location_str = ''
    curl_text = ''

    for subdir in MNT_DIR.iterdir():
        if not subdir.is_dir():
            continue
        area, version = subdir.name.split('-')
        location_str += create_version_location(
            area=area, version=version, subdir=subdir, local=local, domain=domain
        )

        if not curl_text:
            curl_text = (
                '\ntest with:\n'
                f'curl -H "Host: __LOCAL__" -I http://localhost/{area}/{version}/14/8529/5975.pbf\n'
                f'curl -I https://__DOMAIN__/{area}/{version}/14/8529/5975.pbf'
            )

    location_str += create_latest_locations(local=local, domain=domain)

    with open(NGINX_DIR / 'location_static.conf') as fp:
        location_str += '\n' + fp.read()

    return location_str, curl_text


def create_version_location(
    *, area: str, version: str, subdir: Path, local: str, domain: str
) -> str:
    run_dir = DEFAULT_RUNS_DIR / area / version
    if not run_dir.is_dir():
        print(f"  {run_dir} doesn't exists, skipping")
        return ''

    tilejson_path = run_dir / f'tilejson-{local}.json'

    metadata_path = subdir / 'metadata.json'
    if not metadata_path.is_file():
        print(f"  {metadata_path} doesn't exists, skipping")
        return ''

    url_prefix = f'https://{domain}/{area}/{version}'

    subprocess.run(
        [
            sys.executable,
            Path(__file__).parent.parent / 'metadata_to_tilejson.py',
            '--minify',
            metadata_path,
            tilejson_path,
            url_prefix,
        ],
        check=True,
    )

    return f"""
    location = /{area}/{version} {{     # no trailing slash
        alias {tilejson_path};          # no trailing slash

        expires 1w;
        default_type application/json;

        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header Cache-Control public;
    }}

    location /{area}/{version}/ {{      # trailing slash
        alias {subdir}/tiles/;          # trailing slash
        try_files $uri @empty_tile;
        add_header Content-Encoding gzip;

        expires 10y;

        types {{
            application/vnd.mapbox-vector-tile pbf;
        }}

        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header Cache-Control public;
    }}
    """


def create_latest_locations(*, local: str, domain: str) -> str:
    location_str = ''

    local_version_files = OFM_CONFIG_DIR.glob('tileset_version_*.txt')
    for file in local_version_files:
        area = file.stem.split('_')[-1]
        with open(file) as fp:
            version = fp.read().strip()
        print(f'  setting latest version for {area}: {version}')

        run_dir = DEFAULT_RUNS_DIR / area / version
        tilejson_path = run_dir / f'tilejson-{local}.json'
        assert tilejson_path.is_file()

        location_str += f"""
        location = /{area} {{          # no trailing slash
            alias {tilejson_path};       # no trailing slash

            expires 1d;
            default_type application/json;

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header Cache-Control public;
        }}
        """

    return location_str


def write_ledns_reader_script(domain_ledns):
    script = f"""
#!/usr/bin/env bash
export RCLONE_CONFIG=/data/ofm/config/rclone.conf
rclone copyto -v "remote:ofm-private/ledns/{domain_ledns}/ofm_ledns.cert" /data/nginx/certs/ofm_ledns.cert
rclone copyto -v "remote:ofm-private/ledns/{domain_ledns}/ofm_ledns.key" /data/nginx/certs/ofm_ledns.key
    """.strip()

    with open(HTTP_HOST_BIN_DIR / 'ledns_reader.sh', 'w') as fp:
        fp.write(script)
