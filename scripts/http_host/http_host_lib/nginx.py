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
        if not (CERTS_DIR / 'cf.cert').exists() or not (CERTS_DIR / 'cf.key').exists():
            sys.exit('cf.cert or cf.key missing')

        curl_text_mix += create_nginx_conf(
            template_path=NGINX_DIR / 'cf.conf',
            local='ofm_cf',
            domain=domain_cf,
        )

    # processing Let's Encrypt config
    if domain_le:
        le_cert = CERTS_DIR / 'le.cert'
        le_key = CERTS_DIR / 'le.key'

        if not (CERTS_DIR / 'le.cert').exists() or not (CERTS_DIR / 'le.key').exists():
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
                'lego',
                '--accept-tos',
                '--email',
                HOST_CONFIG['le_email'],
                '--http',
                '--http.webroot=/data/nginx/acme-challenges/',
                '--domains',
                domain_le,
                '--http-timeout=30',
                '--path=/data/nginx/lego/',
                'run',
            ],
            check=True,
        )

        # link lego certs to nginx dir
        le_cert.unlink()
        le_key.unlink()
        le_cert.symlink_to(Path(f'/data/nginx/lego/certificates/{domain_le}.crt'))
        le_key.symlink_to(Path(f'/data/nginx/lego/certificates/{domain_le}.key'))

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
        assert tilejson_path.exists()

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
