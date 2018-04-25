from xml.dom import minidom
import os
import re
# https://qiita.com/akabei/items/38f974716f194afea4a5
from flask import Flask, request, abort
import random
import requests
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage,
    VideoMessage, AudioMessage, StickerMessage
)
from Logic import Logic
import atexit


def load_credentials():
    xdoc = minidom.parse("credentials.xml")
    token = xdoc.getElementsByTagName("token")[0].childNodes[0].data
    secret = xdoc.getElementsByTagName("secret")[0].childNodes[0].data
    return (token, secret)


app = Flask(__name__)
app.config['DEBUG'] = False

token, secret = load_credentials()
line_bot_api = LineBotApi(token)
parser = WebhookParser(secret)

past_messages = []


def generate_reply(text):
    print("received\t" + text)
    reply = ""
    # # use random old message
    # past_messages.append(text)
    # print(past_messages)
    # return past_messages[random.randrange(0,len(past_messages))]

    pattern_me = "(私|わたし|俺|僕|自分)"
    pattern_you = "(君|あなた|お前)"
    reply = re.sub(pattern_me, "貴方", text)
    reply = re.sub(pattern_you, "私", reply)
    print("reply\t" + reply)
    return reply


def get_media(msg_id):
    # http://docs.python-requests.org/en/latest/user/quickstart/#make-a-request
    global token
    header = {'Authorization': token}
    payload = {'messageId': msg_id}
    r = requests.get("https://api.line.me/v2/bot/message/" +
                     msg_id + "/content", params=payload, headers=header)
    return r.content


@app.route("/callback", methods=['POST'])
def callback():
    global logic
    print("callback called")
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        print("invalid signature")
        abort(400)

    for event in events:
        print("_________analyzing event_________")
        if event.message.id == "100001":
            print("connection check")
            return 'OK'
        group_id = None
        if event.source.type == "group":
            group_id = event.source.group_id
        elif event.source.type == "room":
            group_id = event.source.room_id
        if logic.identify(event.source.user_id, group_id) < 0:
            print("New user or room.")
            logic.add_room_or_user(line_bot_api.get_profile
                                   (event.source.user_id), group_id)

        if isinstance(event, MessageEvent):
            if isinstance(event.message, TextMessage):
                reply = logic.receive_text(
                    event.source.user_id, group_id, event.message.text)
            elif isinstance(event.message, ImageMessage):
                reply = logic.receive_image(
                    event.source.user_id, group_id,
                    get_media(event.message.id))
            else:
                continue
            line_bot_api.reply_message(
                event.reply_token, reply)

    return 'OK'


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logic = Logic()
    atexit.register(logic.save_log)
    app.run(host="0.0.0.0", port=port)
