import subprocess
import sys
from pathlib import Path

from http_host_lib.config import config
from http_host_lib.slugify import slugify
from http_host_lib.utils import python_venv_executable


def write_nginx_config():
    print('Writing nginx config')

    if not config.mnt_dir.exists():
        sys.exit('  mount needs to be run first')

    # remove old configs and certs
    for file in Path('/data/nginx/sites').glob('ofm_*.conf'):
        file.unlink()

    for file in Path('/data/nginx/certs').glob('ofm_*'):
        file.unlink()

    conf = config.jsonc_config

    curl_help_lines = []

    for domain_data in conf['domains']:
        curl_help_lines += process_domain(domain_data)

    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=True)

    if config.ofm_config.get('skip_planet'):
        curl_help_lines = [l for l in curl_help_lines if '/planet' not in l]
    else:
        curl_help_lines = [l for l in curl_help_lines if '/monaco' not in l]

    curl_help_str = '\n'.join(curl_help_lines)
    print(f'test with:\n{curl_help_str}')


def process_domain(domain_data):
    domain_slug = slugify(domain_data['domain'], separator='_')
    domain_data['slug'] = domain_slug

    if domain_data['cert'] == 'upload':
        domain_data['cert_file'] = config.certs_dir / f'{domain_slug}.cert'
        domain_data['key_file'] = config.certs_dir / f'{domain_slug}.key'

        if not domain_data['cert_file'].is_file() or not domain_data['key_file'].is_file():
            sys.exit(
                f'  cert or key file does not exist: {domain_data["cert_file"]} {domain_data["key_file"]}'
            )

        return create_nginx_conf(domain_data)


def create_nginx_conf(domain_data: dict):
    dynamic_block_lines, curl_text = dynamic_blocks(domain_data)

    template = (config.nginx_confs_templates / 'common.conf').read_text()

    template = template.replace('__DYNAMIC_BLOCKS__', dynamic_block_lines)

    template = template.replace('__DOMAIN_SLUG__', domain_data['slug'])
    template = template.replace('__DOMAIN__', domain_data['domain'])

    curl_text = curl_text.replace('__DOMAIN_SLUG__', domain_data['slug'])
    curl_text = curl_text.replace('__DOMAIN__', domain_data['domain'])

    with open(f'/data/nginx/sites/{domain_data["slug"]}.conf', 'w') as fp:
        fp.write(template)
        print(f'  nginx config written: {domain_data["domain"]} {domain_data["slug"]}')

    return curl_text


def dynamic_blocks(domain_data: dict):
    nginx_conf_lines = ''
    curl_help_lines = []

    for subdir in config.mnt_dir.iterdir():
        if not subdir.is_dir():
            continue
        area, version = subdir.name.split('-')

        nginx_conf_lines += create_version_location(
            area=area, version=version, mnt_dir=subdir, domain_data=domain_data
        )

        for path in [
            f'/{area}/{version}',
            f'/{area}/{version}/14/8529/5975.pbf',
            f'/{area}/{version}/9999/9999/9999.pbf',  # empty_tile test
        ]:
            curl_help_lines += [
                f'curl -H "Host: __DOMAIN_SLUG__" -I http://localhost/{path}',
                f'curl -sI https://__DOMAIN__{path} | sort',
            ]

    nginx_conf_lines += create_latest_locations(domain_data=domain_data)

    for area in config.areas:
        for path in [
            f'/{area}',
            f'/{area}/19700101_old_version_test',
            f'/{area}/19700101_old_version_test/14/8529/5975.pbf',
            f'/{area}/19700101_old_version_test/9999/9999/9999.pbf',  # empty_tile test
        ]:
            curl_help_lines += [
                f'curl -H "Host: __DOMAIN_SLUG__" -I http://localhost/{path}',
                f'curl -sI https://__DOMAIN__{path} | sort',
            ]

    nginx_conf_lines += '\n' + (config.nginx_confs_templates / 'static_blocks.conf').read_text()

    return nginx_conf_lines, curl_help_lines


def create_version_location(*, area: str, version: str, mnt_dir: Path, domain_data: dict) -> str:
    run_dir = config.runs_dir / area / version
    if not run_dir.is_dir():
        print(f"  {run_dir} doesn't exist, skipping")
        return ''

    tilejson_path = run_dir / f'tilejson-{domain_data["slug"]}.json'

    metadata_path = mnt_dir / 'metadata.json'
    if not metadata_path.is_file():
        print(f"  {metadata_path} doesn't exist, skipping")
        return ''

    url_prefix = f'https://{domain_data["domain"]}/{area}/{version}'

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
        add_header X-Robots-Tag "noindex, nofollow" always;

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
        add_header X-Robots-Tag "noindex, nofollow" always;

        add_header x-ofm-debug 'specific PBF {area} {version}';
    }}
    """


def create_latest_locations(*, domain_data: dict) -> str:
    location_str = ''

    local_version_files = config.deployed_versions_dir.glob('*.txt')

    for file in local_version_files:
        area = file.stem
        with open(file) as fp:
            version = fp.read().strip()

        print(f'  linking latest version for {area}: {version}')

        # checking runs dir
        run_dir = config.runs_dir / area / version
        tilejson_path = run_dir / f'tilejson-{domain_data["slug"]}.json'
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
            add_header X-Robots-Tag "noindex, nofollow" always;

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
            try_files /tilejson-{domain_data['slug']}.json =404;

            expires 1w;
            default_type application/json;

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header Cache-Control public;
            add_header X-Robots-Tag "noindex, nofollow" always;

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
            add_header X-Robots-Tag "noindex, nofollow" always;

            add_header x-ofm-debug 'wildcard PBF {area}';
        }}
        """

    return location_str


# if not self_signed_certs:
#     subprocess.run(
#         [
#             'certbot',
#             'certonly',
#             '--webroot',
#             '--webroot-path=/data/nginx/acme-challenges',
#             '--noninteractive',
#             '-m',
#             config.ofm_config['letsencrypt_email'],
#             '--agree-tos',
#             '--cert-name=ofm_direct',
#             # '--staging',
#             '--deploy-hook',
#             'nginx -t && service nginx reload',
#             '-d',
#             domain_direct,
#         ],
#         check=True,
#     )
#
#     # link certs to nginx dir
#     direct_cert.unlink()
#     direct_key.unlink()
#
#     etc_cert = Path('/etc/letsencrypt/live/ofm_direct/fullchain.pem')
#     etc_key = Path('/etc/letsencrypt/live/ofm_direct/privkey.pem')
#     assert etc_cert.is_file()
#     assert etc_key.is_file()
#     direct_cert.symlink_to(etc_cert)
#     direct_key.symlink_to(etc_key)
