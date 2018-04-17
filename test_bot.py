from xml.dom import minidom
# https://qiita.com/akabei/items/38f974716f194afea4a5
def load_credentials():
    xdoc=minidom.parse("credentials.xml")
    token = "C63GEmcb4YrRrr7qx82/eJSSOxKpmHhXQo3cuoMzK2q7924z4IDBdFz82s1sqFZdg9lp2U/nNfxrRSqPukgHmMsw3HqyVCtHYmfqd3B/ogmjiYxuYhpTDIyDURx4IO1quQFAaR/9T0CdMDT86qIiQgdB04t89/1O/w1cDnyilFU="#xdoc.getElementsByTagName("token")[0].childNodes[0].data
    secret= "a4604b99df8bf0df1c06ce0ce1f91a7"#xdoc.getElementsByTagName("secret")[0].childNodes[0].data
    return (token, secret)

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
