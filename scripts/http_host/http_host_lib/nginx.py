import shutil
import subprocess
import sys
from pathlib import Path

from http_host_lib import (
    CERTS_DIR,
    DEFAULT_RUNS_DIR,
    HOST_CONFIG,
    MNT_DIR,
    NGINX_DIR,
    OFM_CONFIG_DIR,
)


def write_nginx_config():
    curl_text_mix = ''

    domain_cf = HOST_CONFIG['domain_cf']
    domain_le = HOST_CONFIG['domain_le']

    # processing Cloudflare config
    if domain_cf:
        if not (CERTS_DIR / 'ofm_cf.cert').is_file() or not (CERTS_DIR / 'ofm_cf.key').is_file():
            sys.exit('ofm_cf.cert or ofm_cf.key missing')

        curl_text_mix += create_nginx_conf(
            template_path=NGINX_DIR / 'cf.conf',
            local='ofm_cf',
            domain=domain_cf,
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
    location_str, curl_text = create_location_blocks()

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


def create_location_blocks():
    location_str = ''
    curl_text = ''

    for subdir in MNT_DIR.iterdir():
        if not subdir.is_dir():
            continue
        area, version = subdir.name.split('-')
        location_str += create_version_location(area, version, subdir)

        if not curl_text:
            curl_text = (
                '\ntest with:\n'
                f'curl -H "Host: __LOCAL__" -I http://localhost/{area}/{version}/14/8529/5975.pbf\n'
                f'curl -I https://__DOMAIN__/{area}/{version}/14/8529/5975.pbf'
            )

    location_str += create_latest_locations()

    with open(NGINX_DIR / 'location_static.conf') as fp:
        location_str += '\n' + fp.read()

    return location_str, curl_text


def create_version_location(area: str, version: str, subdir: Path) -> str:
    run_dir = DEFAULT_RUNS_DIR / area / version
    if not run_dir.is_dir():
        print(f"  {run_dir} doesn't exists, skipping")
        return ''

    tilejson_path = run_dir / 'tilejson-tiles-org.json'

    metadata_path = subdir / 'metadata.json'
    if not metadata_path.is_file():
        print(f"  {metadata_path} doesn't exists, skipping")
        return ''

    url_prefix = f'https://tiles.openfreemap.org/{area}/{version}'

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


def create_latest_locations() -> str:
    location_str = ''

    local_version_files = OFM_CONFIG_DIR.glob('tileset_version_*.txt')
    for file in local_version_files:
        area = file.stem.split('_')[-1]
        with open(file) as fp:
            version = fp.read().strip()
        print(f'  setting latest version for {area}: {version}')

        run_dir = DEFAULT_RUNS_DIR / area / version
        tilejson_path = run_dir / 'tilejson-tiles-org.json'
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
