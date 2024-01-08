import subprocess
import sys
from pathlib import Path

from http_host_lib import DEFAULT_RUNS_DIR, MNT_DIR, OFM_CONFIG_DIR, TEMPLATES_DIR


def write_nginx_config():
    with open(TEMPLATES_DIR / 'nginx_cf.conf') as fp:
        nginx_template = fp.read()

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
                f'curl -H "Host: ofm" -I http://localhost/{area}/{version}/14/8529/5975.pbf\n'
                f'curl -I https://tiles.openfreemap.org/{area}/{version}/14/8529/5975.pbf'
            )

    location_str += create_latest_locations()

    nginx_template = nginx_template.replace('___LOCATION_BLOCKS___', location_str)

    with open('/data/nginx/sites/ofm-tiles-org.conf', 'w') as fp:
        fp.write(nginx_template)
        print('  nginx config written')

    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=True)

    print(curl_text)


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
        default_type application/json;

        expires 1d;  # TODO target 1w

        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header Cache-Control public;
    }}

    location /{area}/{version}/ {{      # trailing slash
        alias {subdir}/tiles/;          # trailing slash
        try_files $uri @empty;
        add_header Content-Encoding gzip;

        expires 1d;  # TODO target 10y

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
            default_type application/json;

            expires 1d;

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header Cache-Control public;
        }}
        """

    return location_str
