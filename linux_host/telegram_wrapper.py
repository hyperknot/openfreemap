from linux_host.config import config
from linux_host.telegram_core import telegram_send_message as telegram_send_message_core


def telegram_send_message(message: str, *, markdown: bool = False) -> None:
    message = f'{config.ofm_host_prefix} {message}'
    print(message)

    if not config.telegram_token or not config.telegram_chat_id:
        print('  Telegram is not configured, skipping notification')
        return

    telegram_send_message_core(
        message,
        config.telegram_token,
        config.telegram_chat_id,
        markdown=markdown,
    )
