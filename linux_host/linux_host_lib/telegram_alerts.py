import socket

from linux_host.linux_host_lib.linux_host_config import get_linux_host_config
from shared_lib.utils.telegram_v2_shared import send_telegram_message


def send_telegram_alert(message: str) -> None:
    message = f'Host: {socket.gethostname()}\n{message}'
    print(message)
    send_telegram_message(
        message,
        token=get_linux_host_config().telegram_token,
        chat_id=get_linux_host_config().telegram_chat_id,
        topic_id=get_linux_host_config().telegram_topic_id,
        header='Linux host',
    )
