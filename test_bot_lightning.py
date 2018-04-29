from xml.dom import minidom
import os
# https://qiita.com/akabei/items/38f974716f194afea4a5
from flask import Flask, request, abort
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
from queue import Queue
from threading import Thread


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


def check_profile(source):
    '''
    analyzes the "source" element of an event
    if it's from a new user or event, adds that to the logic class.
    returns the user_id and group_id(which is None if
    it's not a group chat or chatroom.)
    '''
    user_id = source.user_id
    group_id = None
    if source.type == "group":
        group_id = source.group_id
    elif source.type == "room":
        group_id = source.room_id
    global logic
    if logic.identify(user_id, group_id) < 0:
        print("New user or room. Retrieving info about user from LINE API....")
        prof = line_bot_api.get_profile(user_id)
        logic.add_room_or_user(prof, group_id)
        print("user info retrieved. added user to room.")
    else:
        print("previously added user in a known room.")
    return (user_id, group_id)


def analyze_messages():
    '''
    constantly running, waiting for a message to come into the queue.
    Run as many threads of these as you want.
    '''
    print("waiting for message event...")
    events = eventsQueue.get(block=True)
    print(len(events), "number of events received")
    for event in events:
        replies = []
        user_id, group_id = check_profile(event.source)
        if isinstance(event.message, TextMessage):
            if user_id == "Udeadbeefdeadbeefdeadbeefdeadbeef":
                print("connection check message.")
                continue
            print("message received, Analyzing source...")
            replies.append(logic.receive_text(
                user_id, group_id, event.message.text))
        elif isinstance(event.message, (ImageMessage, VideoMessage, AudioMessage)):
            if isinstance(event.message, ImageMessage):
                ext = '.jpg'
            elif isinstance(event.message, VideoMessage):
                ext = '.mp4'
            else:
                ext = '.m4a'
            replies.append(logic.receive_media(
                user_id, group_id, line_bot_api.get_message_content(event.message.id), ext))
        else:
            continue
        line_bot_api.reply_message(event.reply_token, replies)
    # recursive function!
    logic.save_log()
    analyze_messages()


@app.route("/callback", methods=['POST'])
def callback():
    global logic
    print("something received")
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
        print("")
        eventsQueue.put(events)
    except InvalidSignatureError:
        print("invalid signature")
        abort(400)
    print("returning 'OK'...")
    return 'OK'


if __name__ == "__main__":
    # use queue to store messages until they can be dealt with
    # https://docs.python.org/3.6/library/queue.html
    eventsQueue = Queue(maxsize=100)
    analyze_messages_threads = []
    for i in range(5):
        analyze_messages_threads.append(Thread(target=analyze_messages))
        # this will stop the thread when ctrl-c is called
        # https://stackoverflow.com/questions/11815947/cannot-kill-python-script-with-ctrl-c
        analyze_messages_threads[i].daemon = True
        analyze_messages_threads[i].start()
    port = int(os.getenv("PORT", 5000))
    logic = Logic()
    atexit.register(logic.save_log)
    app.run(host="0.0.0.0", port=port)
    eventsQueue.join()
