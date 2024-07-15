async function sendTelegramMessage(message, botToken, chatId) {
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`
  const payload = {
    chat_id: chatId,
    text: message,
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      console.error('Failed to send message:', await response.text())
    }
  } catch (error) {
    console.error('Error sending Telegram message:', error)
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url)

    if (url.pathname === '/b') {
      url.pathname = '/styles/bright'
    }

    if (!url.pathname.startsWith('/styles')) {
      const errorMessage = 'Bad path'
      return new Response(errorMessage, { status: 500 })
    }

    const proxyUrl = new URL(url.pathname, 'https://tiles.openfreemap.org')

    try {
      const response = await fetch(proxyUrl)

      if (response.status !== 200) {
        const errorMessage = `Proxy error: Bad status ${response.status} ${url.pathname}`
        console.error(errorMessage)
        await sendTelegramMessage(errorMessage, env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID)
        return new Response('Proxy error: Bad status', { status: 500 })
      }

      return response
    } catch (error) {
      const errorMessage = `Proxy error: ${error.message} ${url.pathname}`
      console.error(errorMessage)
      await sendTelegramMessage(errorMessage, env.TELEGRAM_TOKEN, env.TELEGRAM_CHAT_ID)
      return new Response('Proxy error: Fetch failed', { status: 500 })
    }
  },
}
