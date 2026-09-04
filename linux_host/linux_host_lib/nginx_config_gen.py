import subprocess
import sys
from pathlib import Path
from typing import Any

from linux_host.linux_host_lib.linux_host_config import get_linux_host_config
from linux_host.linux_host_lib.metadata_to_tilejson import write_tilejson
from linux_host.linux_host_lib.telegram_alerts import send_telegram_alert


HTTP_REDIRECT_SERVER = """server {
    listen 80;
    listen [::]:80;
    server_name __DOMAIN_SLUG__ __DOMAIN__;

    # ACME HTTP-01 challenge requests are intercepted by ngx_http_acme_module
    # before normal location processing, so regular HTTP traffic can redirect.
    return 308 https://$host$request_uri;
}"""

# Mozilla Guideline v6.0 intermediate config for nginx + OpenSSL 3.x.
# 3.0.2 and 3.0.13 currently generate the same config.
# Do not use the OpenSSL 4.0 X25519MLKEM768 variant yet: current Ubuntu 24.04
# servers with OpenSSL 3.0 reject it in nginx -t.
# https://ssl-config.mozilla.org/#server=nginx&version=1.27.3&config=intermediate&openssl=3.0.2&guideline=6.0
SSL_INTERMEDIATE_CONFIG = """# intermediate configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ecdh_curve X25519:prime256v1:secp384r1;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m; # about 40000 sessions"""

# Do not assume the operator controls every subdomain, and do not preload.
NOINDEX_HEADERS = """add_header X-Robots-Tag "noindex, nofollow" always;
add_header Strict-Transport-Security "max-age=63072000" always;"""

PUBLIC_HEADERS = f"""add_header 'Access-Control-Allow-Origin' '*' always;
add_header Cache-Control public;
{NOINDEX_HEADERS}"""


def write_nginx_config_if_changed(
    retained_versions: dict[str, set[str]], active_versions: dict[str, str]
) -> None:
    print('Writing nginx config')
    get_linux_host_config().mnt_dir.mkdir(parents=True, exist_ok=True)

    desired = {
        f'ofm-{domain_data["slug"]}.conf': create_domain_config(
            domain_data, retained_versions, active_versions
        )
        for domain_data in get_linux_host_config().domains
    }
    existing_files = list(get_linux_host_config().nginx_sites_dir.glob('ofm-*.conf'))
    existing = {path.name: path.read_text() for path in existing_files}
    changed = desired != existing
    if changed:
        for filename, content in desired.items():
            (get_linux_host_config().nginx_sites_dir / filename).write_text(content)
        for path in existing_files:
            if path.name not in desired:
                path.unlink()
    else:
        print('nginx config unchanged')

    # Always validate saved files, but reload only for generated changes. Keeping
    # no persistent reload marker makes stable minutely syncs stateless.
    result = subprocess.run(['nginx', '-t'])
    if result.returncode != 0:
        send_telegram_alert('ERROR\nnginx config test failed')
        result.check_returncode()
    if changed:
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)


def create_domain_config(
    domain_data: dict[str, Any],
    retained_versions: dict[str, set[str]],
    active_versions: dict[str, str],
) -> str:
    cert_type = domain_data['cert']['type']
    if cert_type == 'upload':
        cert_file = Path(f'/data/nginx/certs/ofm-{domain_data["slug"]}.cert')
        key_file = Path(f'/data/nginx/certs/ofm-{domain_data["slug"]}.key')

        if not cert_file.is_file() or not key_file.is_file():
            sys.exit(f'  cert or key file does not exist: {cert_file} {key_file}')

    return create_nginx_conf(domain_data, retained_versions, active_versions)


def create_nginx_conf(
    domain_data: dict[str, Any],
    retained_versions: dict[str, set[str]],
    active_versions: dict[str, str],
) -> str:
    dynamic_block_text = dynamic_blocks(domain_data, retained_versions, active_versions)

    template = (get_linux_host_config().nginx_templates_dir / 'common.conf').read_text()

    template = template.replace('__DYNAMIC_BLOCKS__', dynamic_block_text)
    template = template.replace('__ACME_ISSUER__', acme_issuer(domain_data))
    template = template.replace('__HTTP_REDIRECT_SERVER__', HTTP_REDIRECT_SERVER)
    template = template.replace('__SSL_INTERMEDIATE_CONFIG__', SSL_INTERMEDIATE_CONFIG)
    template = template.replace('__NOINDEX_HEADERS__', NOINDEX_HEADERS)
    template = template.replace('__PUBLIC_HEADERS__', PUBLIC_HEADERS)
    template = template.replace(
        '    __SSL_CERTIFICATE_DIRECTIVES__', ssl_certificate_directives(domain_data)
    )

    template = template.replace('__DOMAIN_SLUG__', domain_data['slug'])
    template = template.replace('__DOMAIN__', domain_data['domain'])

    print(f'  nginx config generated: {domain_data["domain"]} {domain_data["slug"]}')
    return template


def acme_issuer(domain_data: dict[str, Any]) -> str:
    if domain_data['cert']['type'] != 'letsencrypt':
        return ''

    return f"""acme_issuer ofm_{domain_data['slug']} {{
    uri https://acme-v02.api.letsencrypt.org/directory;
    contact mailto:{domain_data['cert']['email']};
    state_path /data/nginx/acme/{domain_data['slug']};
    accept_terms_of_service;
}}"""


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
    ssl_certificate_cache max=10 inactive=1h valid=10m;"""

    raise ValueError(f'Unknown certificate type: {cert_type}')


def dynamic_blocks(
    domain_data: dict[str, Any],
    retained_versions: dict[str, set[str]],
    active_versions: dict[str, str],
) -> str:
    nginx_conf_text = ''

    for area, versions in retained_versions.items():
        for version in sorted(versions):
            mnt_dir = get_linux_host_config().mnt_dir / f'{area}-{version}'
            nginx_conf_text += create_version_location(
                area=area, version=version, mnt_dir=mnt_dir, domain_data=domain_data
            )

    nginx_conf_text += create_latest_locations(
        domain_data=domain_data, active_versions=active_versions
    )

    static_blocks = (get_linux_host_config().nginx_templates_dir / 'static_blocks.conf').read_text()
    static_blocks = static_blocks.replace('__ROOT_REDIRECT_BLOCK__', root_redirect_block())
    nginx_conf_text += '\n' + static_blocks
    return nginx_conf_text


def root_redirect_block() -> str:
    if get_linux_host_config().root_redirect_url:
        return f"""location = / {{
    return 302 {get_linux_host_config().root_redirect_url};
}}
"""

    return """location = / {
    default_type text/plain;
    return 200 'This is an OpenFreeMap tile server.\nhttps://openfreemap.org\n';
}
"""


def create_version_location(
    *, area: str, version: str, mnt_dir: Path, domain_data: dict[str, Any]
) -> str:
    run_dir = get_linux_host_config().versions_dir / area / version
    if not run_dir.is_dir():
        print(f"  {run_dir} doesn't exist, skipping")
        return ''

    tilejson_path = run_dir / f'tilejson-{domain_data["slug"]}.json'

    metadata_path = mnt_dir / 'metadata.json'
    if not metadata_path.is_file():
        print(f"  {metadata_path} doesn't exist, skipping")
        return ''

    url_prefix = f'https://{domain_data["domain"]}/{area}/{version}'

    if not tilejson_path.exists():
        write_tilejson(metadata_path, tilejson_path, url_prefix)

    return f"""
    # specific JSON {area} {version}
    location = /{area}/{version} {{ # no trailing slash
        alias {tilejson_path}; # no trailing slash

        expires 1w;
        default_type application/json;

        {PUBLIC_HEADERS}

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

        {PUBLIC_HEADERS}

        add_header x-ofm-debug 'specific PBF {area} {version}';
    }}
    """


def create_latest_locations(*, domain_data: dict[str, Any], active_versions: dict[str, str]) -> str:
    location_str = ''

    for area, version in active_versions.items():
        print(f'  linking latest version for {area}: {version}')

        run_dir = get_linux_host_config().versions_dir / area / version
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

            {PUBLIC_HEADERS}

            add_header x-ofm-debug 'latest JSON {area}';
        }}
        """

        # Missing version URLs intentionally fall back to the active version.
        # This bounded-storage policy accepts mixed responses from shared caches.
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

            {PUBLIC_HEADERS}

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

            {PUBLIC_HEADERS}

            add_header x-ofm-debug 'wildcard PBF {area}';
        }}
        """

    return location_str
