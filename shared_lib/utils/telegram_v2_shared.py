"""Generic Telegram Bot API message sender."""

import re

import requests


# Telegram limits sendMessage text to 4,096 characters after entity parsing.
TELEGRAM_MESSAGE_LIMIT = 4096
_TRUNCATION_MARKER = '\n\n[message truncated]\n\n'


def send_telegram_message(
    message: str,
    *,
    token: str | None,
    chat_id: str | None,
    topic_id: int | None = None,
    header: str | None = None,
) -> None:
    """Send literal text with an optional bold MarkdownV2 header."""
    # Alerts must not hide the original failure when optional config is absent.
    if not token or not chat_id:
        print('[telegram] credentials missing; message not sent')
        return

    # Telegram applies its limit after parsing Markdown, so escape characters
    # and bold delimiters do not count. Only reserve the visible header length.
    body_limit = TELEGRAM_MESSAGE_LIMIT - (len(header) + 1 if header else 0)
    body = _escape_markdown(_truncate_message(message, body_limit))

    # Escape user text before adding Markdown delimiters. Error messages often
    # contain reserved punctuation that would otherwise reject the request.
    text = f'*{_escape_markdown(header)}*\n{body}' if header else body

    payload: dict[str, object] = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'MarkdownV2',
        'disable_web_page_preview': True,
    }
    # Telegram forum topics use message_thread_id; omit it for ordinary chats.
    if topic_id is not None:
        payload['message_thread_id'] = topic_id

    # Notification delivery is best effort. A Telegram or network failure must
    # not replace the application exception that caused the alert.
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json=payload,
            timeout=5,
        )
        if response.status_code != 200:
            print(f'[telegram] {response.text}')
    except requests.RequestException as exc:
        print(f'[telegram] {exc}')


def _escape_markdown(text: str) -> str:
    # This is Telegram's required MarkdownV2 reserved-character set. Include a
    # backslash itself so arbitrary input cannot create an escape sequence.
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)


def _truncate_message(message: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> str:
    if len(message) <= limit:
        return message

    # Keep both ends: the summary is normally first and useful exception detail
    # or a path is often last. The marker makes truncation visible to operators.
    available = limit - len(_TRUNCATION_MARKER)
    head_length = available // 2
    tail_length = available - head_length
    return message[:head_length] + _TRUNCATION_MARKER + message[-tail_length:]
