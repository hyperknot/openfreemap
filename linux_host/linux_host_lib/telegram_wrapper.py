from linux_host.linux_host_lib.linux_host_config import linux_host_config
from linux_host.linux_host_lib.telegram_core import (
    telegram_send_message as telegram_send_message_core,
)


def telegram_send_message(message: str, *, markdown: bool = False) -> None:
    message = f'{linux_host_config.ofm_host_prefix} {message}'
    print(message)

    if not linux_host_config.telegram_token or not linux_host_config.telegram_chat_id:
        print('  Telegram is not configured, skipping notification')
        return

    telegram_send_message_core(
        message,
        linux_host_config.telegram_token,
        linux_host_config.telegram_chat_id,
        markdown=markdown,
    )
