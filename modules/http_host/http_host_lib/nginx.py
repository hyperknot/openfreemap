import shutil
import subprocess
import sys
from pathlib import Path

from http_host_lib.config import config
from http_host_lib.utils import python_venv_executable


def write_nginx_config():
    if not config.mnt_dir.exists():
        sys.exit('  mount needs to be run first')

    curl_text_mix = ''

    domain_le = config.ofm_config['domain_le']
    domain_ledns = config.ofm_config['domain_ledns']

    # remove old configs and certs
    for file in Path('/data/nginx/sites').glob('ofm_*.conf'):
        file.unlink()

    for file in Path('/data/nginx/certs').glob('ofm_*'):
        file.unlink()

    # processing Round Robin DNS config
    if domain_ledns:
        if not config.rclone_config.is_file():
            sys.exit('rclone.conf missing')

        # download the ledns certificate from bucket using rclone
        write_ledns_reader_script(domain_ledns)
        subprocess.run(['bash', config.http_host_bin / 'ledns_reader.sh'], check=True)

        curl_text_mix += create_nginx_conf(
            template_path=config.nginx_confs / 'ledns.conf',
            local='ofm_ledns',
            domain=domain_ledns,
        )

    # processing Let's Encrypt config
    if domain_le:
        le_cert = config.certs_dir / 'ofm_le.cert'
        le_key = config.certs_dir / 'ofm_le.key'

        if not le_cert.is_file() or not le_key.is_file():
            shutil.copyfile(Path('/etc/nginx/ssl/dummy.crt'), le_cert)
            shutil.copyfile(Path('/etc/nginx/ssl/dummy.key'), le_key)

        curl_text_mix += create_nginx_conf(
            template_path=config.nginx_confs / 'le.conf',
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
                config.ofm_config['le_email'],
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

    curl_text_lines = sorted(curl_text_mix.splitlines())
    if '/monaco' in curl_text_mix:
        curl_text_lines = [l for l in curl_text_lines if '/monaco' not in l]

    curl_text_mix = '\n'.join(curl_text_lines)
    print(f'test with:\n{curl_text_mix}')


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

    for subdir in config.mnt_dir.iterdir():
        if not subdir.is_dir():
            continue
        area, version = subdir.name.split('-')

        location_str += create_version_location(
            area=area, version=version, mnt_dir=subdir, local=local, domain=domain
        )

        for path in [
            f'/{area}/{version}',
            f'/{area}/{version}/14/8529/5975.pbf',
            f'/{area}/{version}/9999/9999/9999.pbf',  # empty_tile test
        ]:
            curl_text += (
                # f'curl -H "Host: __LOCAL__" -I http://localhost/{path}\n'
                f'curl -sI https://__DOMAIN__{path} | sort\n'
            )

    location_str += create_latest_locations(local=local, domain=domain)

    for area in config.areas:
        for path in [
            f'/{area}',
            f'/{area}/19700101_old_version_test',
            f'/{area}/19700101_old_version_test/14/8529/5975.pbf',
            f'/{area}/19700101_old_version_test/9999/9999/9999.pbf',  # empty_tile test
        ]:
            curl_text += (
                # f'curl -H "Host: __LOCAL__" -I http://localhost/{path}\n'
                f'curl -sI https://__DOMAIN__{path} | sort\n'
            )

    with open(config.nginx_confs / 'location_static.conf') as fp:
        location_str += '\n' + fp.read()

    return location_str, curl_text


def create_version_location(
    *, area: str, version: str, mnt_dir: Path, local: str, domain: str
) -> str:
    run_dir = config.runs_dir / area / version
    if not run_dir.is_dir():
        print(f"  {run_dir} doesn't exists, skipping")
        return ''

    tilejson_path = run_dir / f'tilejson-{local}.json'

    metadata_path = mnt_dir / 'metadata.json'
    if not metadata_path.is_file():
        print(f"  {metadata_path} doesn't exists, skipping")
        return ''

    url_prefix = f'https://{domain}/{area}/{version}'

    subprocess.run(
        [
            python_venv_executable(),
            config.http_host_scripts_dir / 'metadata_to_tilejson.py',
            '--minify',
            metadata_path,
            tilejson_path,
            url_prefix,
        ],
        check=True,
    )

    return f"""
    # specific JSON {area} {version}
    location = /{area}/{version} {{ # no trailing slash
        alias {tilejson_path}; # no trailing slash

        expires 1w;
        default_type application/json;

        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header Cache-Control public;

        add_header x-ofm-debug 'specific JSON {area} {version}';
    }}

    # specific PBF {area} {version}
    location ^~ /{area}/{version}/ {{ # trailing slash
        alias {mnt_dir}/tiles/; # trailing slash
        try_files $uri @empty_tile;
        add_header Content-Encoding gzip;

        expires 10y;

        types {{
            application/vnd.mapbox-vector-tile pbf;
        }}

        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header Cache-Control public;

        add_header x-ofm-debug 'specific PBF {area} {version}';
    }}
    """


def create_latest_locations(*, local: str, domain: str) -> str:
    location_str = ''

    local_version_files = config.deployed_versions_dir.glob('*.txt')

    for file in local_version_files:
        area = file.stem
        with open(file) as fp:
            version = fp.read().strip()

        print(f'  linking latest version for {area}: {version}')

        # checking runs dir
        run_dir = config.runs_dir / area / version
        tilejson_path = run_dir / f'tilejson-{local}.json'
        if not tilejson_path.is_file():
            print(f'    error with latest: {tilejson_path} does not exist')
            continue

        # checking mnt dir
        mnt_dir = Path(f'/mnt/ofm/{area}-{version}')
        mnt_file = mnt_dir / 'metadata.json'
        if not mnt_file.is_file():
            print(f'    error with latest: {mnt_file} does not exist')
            continue

        # latest
        location_str += f"""

        # latest JSON {area}
        location = /{area} {{ # no trailing slash
            alias {tilejson_path}; # no trailing slash

            expires 1d;
            default_type application/json;

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header Cache-Control public;

            add_header x-ofm-debug 'latest JSON {area}';
        }}
        """

        # wildcard
        # identical to create_version_location
        location_str += f"""

        # wildcard JSON {area}
        location ~ ^/{area}/([^/]+)$ {{
            # regex location is unreliable with alias, only root is reliable

            root {run_dir}; # no trailing slash
            try_files /tilejson-{local}.json =404;

            expires 1w;
            default_type application/json;

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header Cache-Control public;

            add_header x-ofm-debug 'wildcard JSON {area}';
        }}

        # wildcard PBF {area}
        location ~ ^/{area}/([^/]+)/(.+)$ {{
            # regex location is unreliable with alias, only root is reliable

            root {mnt_dir}/tiles/; # trailing slash
            try_files /$2 @empty_tile;
            add_header Content-Encoding gzip;

            expires 10y;

            types {{
                application/vnd.mapbox-vector-tile pbf;
            }}

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header Cache-Control public;

            add_header x-ofm-debug 'wildcard PBF {area}';
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

    with open(config.http_host_bin / 'ledns_reader.sh', 'w') as fp:
        fp.write(script)
