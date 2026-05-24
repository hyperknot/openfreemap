import hashlib
import json
import socket
import time
from pathlib import Path

import requests

from http_host_lib.config import config


DEFAULT_COOLDOWN_SECONDS = 6 * 60 * 60


def telegram_send_message(message: str) -> bool:
    print(message)

    if not _telegram_configured():
        print('  Telegram is not configured, skipping notification')
        return False

    url = f'https://api.telegram.org/bot{config.json_config["telegram_token"]}/sendMessage'
    payload = {'chat_id': config.json_config['telegram_chat_id'], 'text': message}

    try:
        response = requests.post(url, data=payload, timeout=20)
    except Exception as e:
        print(f'  Failed to send Telegram message: {type(e).__name__}: {e}')
        return False

    if response.status_code == 200:
        print('  Telegram message sent successfully')
        return True

    print(f'  Failed to send Telegram message: {response.text}')
    return False


def telegram_notify_throttled(
    key: str,
    message: str,
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
) -> bool:
    if not _telegram_configured():
        return telegram_send_message(message)

    now = time.time()
    state_file = _state_file()
    state = _read_state(state_file)
    last_sent = state[key]['last_sent'] if key in state else 0

    if now - last_sent < cooldown_seconds:
        print(f'  Telegram notification throttled for key: {key}')
        return False

    sent = telegram_send_message(message)
    state[key] = {
        'last_sent': now,
        'sent': sent,
        'message_hash': hashlib.sha256(message.encode()).hexdigest(),
    }
    _write_state(state_file, state)
    return sent


def ofm_host_prefix() -> str:
    return f'OFM http_host {socket.gethostname()}'


def _telegram_configured() -> bool:
    return 'telegram_token' in config.json_config and 'telegram_chat_id' in config.json_config


def _state_file() -> Path:
    return config.http_host_dir / 'logs' / 'telegram_notifications.json'


def _read_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _write_state(path: Path, state: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2, sort_keys=True))
    except Exception as e:
        print(f'  Failed to write Telegram throttle state: {type(e).__name__}: {e}')
