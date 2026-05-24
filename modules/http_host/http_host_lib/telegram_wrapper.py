from http_host_lib.config import config
from http_host_lib.telegram_core import telegram_send_message as telegram_send_message_core


def telegram_send_message(message: str, *, markdown: bool = False) -> None:
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
