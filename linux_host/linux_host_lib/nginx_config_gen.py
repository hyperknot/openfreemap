import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from linux_host.linux_host_lib.linux_host_config import linux_host_config
from linux_host.linux_host_lib.utils import python_venv_executable


def write_nginx_config():
    print('Writing nginx config')

    if not linux_host_config.mnt_dir.exists():
        sys.exit('  mount needs to be run first')

    # remove old configs
    for file in linux_host_config.nginx_sites_dir.glob('ofm-*.conf'):
        file.unlink()
    acme_config_path = Path('/data/nginx/config/ofm-acme.conf')
    if acme_config_path.exists():
        acme_config_path.unlink()

    write_acme_config()

    curl_help_text = ''

    for domain_data in linux_host_config.domains:
        curl_help_text += process_domain(domain_data)

    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
    warm_up_letsencrypt_certs()

    exclude_path = '/planet' if linux_host_config.skip_planet else '/monaco'
    curl_help_lines = [l for l in curl_help_text.splitlines() if exclude_path not in l]

    curl_help_joined = '\n'.join(curl_help_lines)
    print(f'test with:\n{curl_help_joined}')


def write_acme_config() -> None:
    domains = letsencrypt_domains()
    if not domains:
        return

    blocks = [
        'resolver 1.1.1.1 8.8.8.8 ipv6=off;',
        'acme_shared_zone zone=ofm_acme:1M;',
    ]
    for domain_data in domains:
        blocks.append(
            f"""
acme_issuer ofm_{domain_data['slug']} {{
    uri https://acme-v02.api.letsencrypt.org/directory;
    contact mailto:{domain_data['cert']['email']};
    state_path /data/nginx/acme/{domain_data['slug']};
    accept_terms_of_service;
}}""".strip()
        )

    Path('/data/nginx/config/ofm-acme.conf').write_text('\n\n'.join(blocks) + '\n')


def warm_up_letsencrypt_certs() -> None:
    reload_needed = False

    for domain_data in letsencrypt_domains():
        if has_letsencrypt_cert(domain_data):
            continue

        print(f'  requesting letsencrypt certificate: {domain_data["domain"]}')
        subprocess.run(
            [
                'curl',
                '-kfsS',
                '--max-time',
                '10',
                '--resolve',
                f'{domain_data["domain"]}:443:127.0.0.1',
                f'https://{domain_data["domain"]}/',
                '-o',
                '/dev/null',
            ],
            check=False,
        )

        for _ in range(30):
            if has_letsencrypt_cert(domain_data):
                print(f'  letsencrypt certificate ready: {domain_data["domain"]}')
                reload_needed = True
                break
            time.sleep(1)
        else:
            print(f'  letsencrypt certificate not ready yet: {domain_data["domain"]}')

    if reload_needed:
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)


def letsencrypt_domains() -> list[dict[str, Any]]:
    return [
        domain_data
        for domain_data in linux_host_config.domains
        if domain_data['cert']['type'] == 'letsencrypt'
    ]


def has_letsencrypt_cert(domain_data: dict[str, Any]) -> bool:
    return any(Path(f'/data/nginx/acme/{domain_data["slug"]}').glob('*.crt'))


def process_domain(domain_data: dict[str, Any]) -> str:
    cert_type = domain_data['cert']['type']
    if cert_type == 'upload':
        cert_file = Path(f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert')
        key_file = Path(f'/data/nginx/certs/ofm-{domain_data["slug"]}.key')

        if not cert_file.is_file() or not key_file.is_file():
            sys.exit(f'  cert or key file does not exist: {cert_file} {key_file}')

    return create_nginx_conf(domain_data)


def create_nginx_conf(domain_data: dict[str, Any]) -> str:
    dynamic_block_text, curl_help_text = dynamic_blocks(domain_data)

    template = (linux_host_config.nginx_templates_dir / 'common.conf').read_text()

    template = template.replace('__DYNAMIC_BLOCKS__', dynamic_block_text)
    template = template.replace(
        '    __SSL_CERTIFICATE_DIRECTIVES__', ssl_certificate_directives(domain_data)
    )

    template = template.replace('__DOMAIN_SLUG__', domain_data['slug'])
    template = template.replace('__DOMAIN__', domain_data['domain'])

    curl_help_text = curl_help_text.replace('__DOMAIN_SLUG__', domain_data['slug'])
    curl_help_text = curl_help_text.replace('__DOMAIN__', domain_data['domain'])

    (linux_host_config.nginx_sites_dir / f'ofm-{domain_data["slug"]}.conf').write_text(template)
    print(f'  nginx config written: {domain_data["domain"]} {domain_data["slug"]}')

    return curl_help_text


def ssl_certificate_directives(domain_data: dict[str, Any]) -> str:
    cert_type = domain_data['cert']['type']
    if cert_type == 'upload':
        return f"""    ssl_certificate /data/nginx/certs/ofm-{domain_data['slug']}.cert;
    ssl_certificate_key /data/nginx/certs/ofm-{domain_data['slug']}.key;"""

    if cert_type == 'dummy':
        return """    ssl_certificate /etc/nginx/ssl/self_signed.cert;
    ssl_certificate_key /etc/nginx/ssl/self_signed.key;"""

    if cert_type == 'letsencrypt':
        return f"""    acme_certificate ofm_{domain_data['slug']} {domain_data['domain']} key=ecdsa:256;
    ssl_certificate $acme_certificate;
    ssl_certificate_key $acme_certificate_key;
    ssl_certificate_cache max=2;"""

    raise ValueError(f'Unknown certificate type: {cert_type}')


def dynamic_blocks(domain_data: dict[str, Any]) -> tuple[str, str]:
    nginx_conf_text = ''
    curl_help_text = ''

    help_area = 'monaco' if linux_host_config.skip_planet else 'planet'

    for subdir in linux_host_config.mnt_dir.iterdir():
        if not subdir.is_dir():
            continue
        area, version = subdir.name.split('-')

        nginx_conf_text += create_version_location(
            area=area, version=version, mnt_dir=subdir, domain_data=domain_data
        )

        if area == help_area:
            for path in [
                f'/{area}/{version}',
                f'/{area}/{version}/14/8529/5974.pbf',
                # f'/{area}/{version}/9999/9999/9999.pbf',  # empty_tile test
            ]:
                # curl_help_text += f'curl -H "Host: __DOMAIN_SLUG__" -I http://localhost{path}\n'
                curl_help_text += f'curl -sI https://__DOMAIN__{path}\n'

    nginx_conf_text += create_latest_locations(domain_data=domain_data)

    for path in [
        f'/{help_area}',
        f'/{help_area}/latest',
        f'/{help_area}/latest/14/8529/5974.pbf',
        # f'/{help_area}/latest/9999/9999/9999.pbf',  # empty_tile test
    ]:
        # curl_help_text += f'curl -H "Host: __DOMAIN_SLUG__" -I http://localhost{path}\n'
        curl_help_text += f'curl -sI https://__DOMAIN__{path}\n'

    nginx_conf_text += (
        '\n' + (linux_host_config.nginx_templates_dir / 'static_blocks.conf').read_text()
    )
    return nginx_conf_text, curl_help_text


def create_version_location(
    *, area: str, version: str, mnt_dir: Path, domain_data: dict[str, Any]
) -> str:
    run_dir = linux_host_config.runs_dir / area / version
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
            linux_host_config.scripts_dir / 'metadata_to_tilejson.py',
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


def create_latest_locations(*, domain_data: dict[str, Any]) -> str:
    location_str = ''

    local_version_files = linux_host_config.deployed_versions_dir.glob('*.txt')

    for file in local_version_files:
        area = file.stem
        with open(file) as fp:
            version = fp.read().strip()

        print(f'  linking latest version for {area}: {version}')

        # checking runs dir
        run_dir = linux_host_config.runs_dir / area / version
        tilejson_path = run_dir / f'tilejson-{domain_data["slug"]}.json'
        if not tilejson_path.is_file():
            print(
                f'    skipping latest block for {area} / {version}: {tilejson_path} does not exist'
            )
            continue

        # checking mnt dir
        mnt_dir = Path(f'/mnt/ofm/{area}-{version}')
        mnt_file = mnt_dir / 'metadata.json'
        if not mnt_file.is_file():
            print(f'    skipping latest block for {area} / {version}: {mnt_file} does not exist')
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
#             linux_host_config.ofm_config['letsencrypt_email'],
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
