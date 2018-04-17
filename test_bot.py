from xml.dom import minidom
# https://qiita.com/akabei/items/38f974716f194afea4a5
def load_credentials():
    xdoc=minidom.parse("credentials.xml")
    token = "C63GEmcb4YrRrr7qx82/eJSSOxKpmHhXQo3cuoMzK2q7924z4IDBdFz82s1sqFZdg9lp2U/nNfxrRSqPukgHmMsw3HqyVCtHYmfqd3B/ogmjiYxuYhpTDIyDURx4IO1quQFAaR/9T0CdMDT86qIiQgdB04t89/1O/w1cDnyilFU="#xdoc.getElementsByTagName("token")[0].childNodes[0].data
    secret= "a4604b99df8bf0df1c06ce0ce1f91a7"#xdoc.getElementsByTagName("secret")[0].childNodes[0].data
    return (token, secret)
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

token, secret=load_credentials()
line_bot_api = LineBotApi(token)
handler = WebhookHandler(secret)


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
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()
