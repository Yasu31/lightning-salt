from xml.dom import minidom
import os
# https://qiita.com/akabei/items/38f974716f194afea4a5
def load_credentials():
    xdoc=minidom.parse("credentials.xml")
    token = xdoc.getElementsByTagName("token")[0].childNodes[0].data
    secret= xdoc.getElementsByTagName("secret")[0].childNodes[0].data
    return (token, secret)
from flask import Flask, request, abort
import random

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)
app.config['DEBUG']=False

token, secret=load_credentials()
line_bot_api = LineBotApi(token)
parser = WebhookParser(secret)

past_messages=[]
def generate_reply(text):
    past_messages.append(text)
    print(past_messages)
    return past_messages[random.randrange(0,len(past_messages))]


@app.route("/callback", methods=['POST'])
def callback():
    print("callback called")
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events=parser.parse(body, signature)
    except InvalidSignatureError:
        print("invalid signature")
        abort(400)

    for event in events:
        print("analyzing event...")
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        reply_text=generate_reply(event.message.text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    return 'OK'


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
