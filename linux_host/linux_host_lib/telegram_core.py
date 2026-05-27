import requests


def telegram_send_message(
    message: str, bot_token: str, chat_id: str, *, markdown: bool = False
) -> None:
    if markdown:
        message = _telegram_escape_markdown(message)

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    payload: dict[str, str | bool] = {
        'chat_id': chat_id,
        'text': message,
        'disable_web_page_preview': True,
    }
    if markdown:
        payload['parse_mode'] = 'MarkdownV2'

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print('Message sent successfully!\n')
    else:
        print('Failed to send message:', response.text, '\n')


def _telegram_escape_markdown(text: str) -> str:
    markdown_v2_escapes = r'\\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in markdown_v2_escapes else char for char in text)
