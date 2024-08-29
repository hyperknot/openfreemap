import requests


def telegram_send_message(message, bot_token, chat_id):
    print(message)

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    payload = {'chat_id': chat_id, 'text': message}

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print('  Message sent successfully!')
    else:
        print('  Failed to send message:', response.text)
