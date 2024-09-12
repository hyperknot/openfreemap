import json
from pathlib import Path

from dotenv import dotenv_values


class Configuration:
    areas = ['planet', 'monaco']

    if Path('/data/ofm').exists():
        ofm_config_dir = Path('/data/ofm/config')
    else:
        repo_root = Path(__file__).parent.parent.parent.parent
        ofm_config_dir = repo_root / 'config'

    ofm_config = json.loads((ofm_config_dir / 'config.json').read_text())

    http_host_list = ofm_config['http_host_list']
    telegram_token = ofm_config['telegram_token']
    telegram_chat_id = ofm_config['telegram_chat_id']

    domain_ledns = ofm_config['domain_ledns']
    domain_root = '.'.join(domain_ledns.split('.')[-2:])

    cloudflare_ini = dotenv_values(ofm_config_dir / 'cloudflare.ini')
    cloudflare_api_token = cloudflare_ini['dns_cloudflare_api_token']


config = Configuration()
