import time
from linebot.models import (
    TextSendMessage
)
import os
import random


class Logic:
    '''
    Deals with the meat and bones of the chatbot.
    '''

    def __init__(self, debug=True):
        '''
        debug: prints debug statements at each step.
        '''
        self.rooms = []
        self.debug = debug
        # for identifying this particular session later
        self.id = int(time.time())
        # this is for saving every single text received, for training later.
        self.all_messages = []

    def receive_text(self, user_id, group_id, text):
        '''
        Before calling this, use the identify() method to check if
        it's a new user or room, and if so, add_room_or_user()
        Input:
        user_id
        group_id: None if it's a single user chat.
        text

        Output:
        reply: message to reply(returned as TextMessage)
        '''
        self.print_debug("received text!")
        self.all_messages.append(text)
        i = self.identify(user_id, group_id)
        rep_text = "エラー"
        if i >= 0:
            self.rooms[i].receive_text(user_id, text)
            rep_text = self.rooms[i].messages_list[random.randint(
                0, len(self.rooms[i].messages_list) - 1)]
            self.rooms[i].send_text(rep_text)
            self.print_debug(self.rooms[i].messages_log)
        return TextSendMessage(text=rep_text)

    def receive_media(self, user_id, group_id, r, ext):
        filename = str(int(time.time())) + ext
        room_num = self.identify(user_id, group_id)
        if ext == '.jpg':
            # received image
            self.make_room_path(self.rooms[room_num].id)
            print("saving image to file...")
            with open("log/" + str(self.rooms[room_num].id) + "/" + filename, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)
            print("finished saving.")
        self.rooms[room_num].receive_text(user_id, filename)
        text = "画像送ってくれたね、でも今は画像で返信できない><"
        self.rooms[room_num].send_text(text)
        return TextSendMessage(text=text)

    def identify(self, user_id, group_id):
        '''
        group_id: None if it's a single user chat.
        Sees the current list of rooms and checks if
        the same user has already contacted before.
        If so, returns the room number. If not, returns -1
        *Note: even if it's the same user, if it comes from
        different rooms it's counted as a different user.
        '''
        self.print_debug("trying to identify user id:" +
                         str(user_id) + ", group_id:" + str(group_id))
        if group_id is None:
            self.print_debug("It's a solo chat room.")
            for i in range(len(self.rooms)):
                if self.rooms[i].id == user_id:
                    # the id of a room is the user_id, if it's a solo chat room
                    self.print_debug("User found in room " + str(i))
                    return i
            self.print_debug("new solo user!")
            return -1
        else:
            self.print_debug("It's a group chat room.")
            for i in range(len(self.rooms)):
                if self.rooms[i].id == group_id:
                    self.print_debug("Identified the room. Now checking if\
                                     the user has already spoken in that room")
                    if self.rooms[i].identify(user_id) >= 0:
                        self.print_debug("User found in room " + str(i))
                        return i
                    self.print_debug("New user in old room!")
                    return -1
            self.print_debug("New room!")
            return -1

    def add_room_or_user(self, profile, group_id=None):
        self.print_debug("adding new user")
        if group_id is None:
            self.print_debug("Is a new indivisual")
            self.rooms.append(Room(profile.user_id))
            self.rooms[len(self.rooms) - 1].add_user(profile)
        else:
            self.print_debug("Is a new room or new user in old room")
            for room in self.rooms:
                if room.id == group_id:
                    self.print_debug("new user in old room!")
                    room.add_user(profile)
                    return
            self.print_debug("Is a new room!")
            self.rooms.append(Room(group_id))
            self.rooms[len(self.rooms) - 1].add_user(profile)

    def print_debug(self, text):
        if self.debug:
            print(text)

    def make_default_path(self):
        self.print_debug("making log directory...")
        # make directories if they don't exist yet.
        if not os.path.exists("log"):
            # https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
            os.makedirs("log")
        if not os.path.exists("log/all_received_messages"):
            os.makedirs("log/all_received_messages")

    def make_room_path(self, room_id):
        if not os.path.exists("log/" + str(room_id)):
            os.makedirs("log/" + str(room_id))
        if not os.path.exists("log/" + str(room_id) + "/all_received_messages"):
            os.makedirs("log/" + str(room_id) + "/all_received_messages")

    def save_log(self):
        '''
        saves logs of conversations
        '''
        self.make_default_path()
        file = open("log/all_received_messages/" + str(self.id) + ".txt", 'w')
        for message in self.all_messages:
            file.write(message + str("\n"))
        file.close()
        for room in self.rooms:
            self.make_room_path(room.id)
            file = open("log/" + str(room.id) + "/" +
                        str(self.id) + ".txt", 'w')
            file.write(room.messages_log)
            file.close()
            file = open("log/" + str(room.id) +
                        "/all_received_messages.txt", 'a')
            for line in room.messages_list:
                file.write(line + "\n")
            file.close()


class Room:
    '''
    Consolidates information about a talk room.
    Mostly just for logging purposes.
    '''

    def __init__(self, id, solo=True):
        '''
        If one-on-one talk, id is the user id.
        in other cases, id is the group/chatroom id.
        '''
        self.id = id
        self.users = []
        self.messages_log = ""
        self.messages_list = []
        self.initialize_messages()

    def identify(self, user_id):
        '''
        returns the index if identified
        -1 if not (new user in group).
        When it's -1, send the data of the person's profile to add_user().
        '''
        for i in range(len(self.users)):
            if self.users[i].user_id == user_id:
                return i
        return -1

    def add_user(self, profile):
        self.users.append(User(profile))

    def receive_text(self, user_id, text):
        '''
        when the bot receives a text message from the user.
        Special cases: when text is "IMAGE" or "VIDEO" or "AUDIO"
        '''
        name = "John Doe??"
        i = self.identify(user_id)
        if i >= 0:
            name = self.users[i].display_name
        if text[-3:] == "jpg" or text[-3:] == "mp4" or text[-3:] == "m4a":
            self.messages_log += (name + "\t" + self.get_time() +
                                  "\t" + text + "\n")
            return
        self.messages_log += (name + "\t" +
                              self.get_time() + "\t" + text + "\n")
        self.messages_list.append(text)

    def send_text(self, text):
        '''
        when the bot sends a text message to the user
        '''
        self.messages_log += ("BOT\t" + self.get_time() + "\t" + text + "\n")

    def initialize_messages(self):
        cur_time = time.localtime()
        self.messages_log += (str(cur_time.tm_year) + "年" +
                              str(cur_time.tm_mon) + "月" +
                              str(cur_time.tm_mday)
                              + "日" + "\n")
        try:
            file = open("log/" + self.id + "/all_received_messages.txt", 'r')
            print("loading previous logs")
            self.messages_list = file.readlines()
        except FileNotFoundError:
            self.messages_list = ["こんにちは！", "ヨロです"]

    def get_time(self):
        cur_time = time.localtime()
        return (str(cur_time.tm_mon) + "月" + str(cur_time.tm_mday)
                + "日" + str(cur_time.tm_hour) + "時" + str(cur_time.tm_min)
                + "分")


class User:
    def __init__(self, profile):
        '''
        get the profile with
        profile = line_bot_api.get_profile(user_id)
        '''
        self.user_id = profile.user_id
        self.display_name = profile.display_name
        self.picture_url = profile.picture_url
        self.status_message = profile.status_message
