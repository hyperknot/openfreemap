from telegram import Bot


bot = Bot(token='YOUR_BOT_TOKEN')

# Replace 'CHAT_ID' with the chat ID you want to send the message to
chat_id = 'CHAT_ID'

# The message you want to send
message = 'Hello, this is a test message from my bot!'

bot.send_message(chat_id=chat_id, text=message)
