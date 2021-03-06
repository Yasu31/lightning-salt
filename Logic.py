import time
from linebot.models import (
    TextSendMessage
)
import os
import random
from Parser import FilesManager
from NeuralNetwork import NeuralNetwork
import numpy as np
import re


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
        self.nn = NeuralNetwork("okan")
        self.nn.prepare()
        # for identifying this particular session later
        self.id = int(time.time())
        # this is for saving every single text received, for training later.
        self.all_unlogged_messages = []  # messages not saved in all_received_messages
        self.filesmanager = FilesManager()
        self.make_paths()
        self.phrases = self.filesmanager.load_phrases()

    def decode(self, nn_prediction, debug=False):
        '''
        decode the output from the neural network.
        Input is the numpy array from the network.
        Output is the list of the possible phrases.
        '''
        argsort = np.argsort(nn_prediction[0])[::-1]
        # the indices in a list, from biggest to smallest.
        top_two = argsort[:2]
        self.print_debug("top two indices and their probabilities:")
        for each in top_two:
            self.print_debug("index:"+str(each)+"\t" +
                             str(nn_prediction[0, each]))
        try:
            if not debug:
                random = np.random.rand()
                if random < nn_prediction[0, top_two[0]]/(nn_prediction[0, top_two[0]] + nn_prediction[0, top_two[1]]):
                    phrase_list = self.phrases[top_two[0]]
                else:
                    phrase_list = self.phrases[top_two[1]]
            else:
                # print the probabilities too
                phrase_list = ""
                for i in range(3):
                    phrase_list += str(nn_prediction[0, argsort[i]]) + \
                        "\t"+str(self.phrases[argsort[i]])+"\n"
        except KeyError:
            phrase_list = ["エラーだわ、すまんw"]
        return phrase_list

    def substitute(self, phrase_list, user_id, group_id):
        '''
        substitutes phrases as appropriate
        '''
        return_list = []
        group_indicator = "(random_name|random_past_msg)"
        room_index = self.identify(user_id, group_id)
        name = self.rooms[room_index].users[self.rooms[room_index].identify(
            user_id)].display_name
        for phrase in phrase_list:
            if (group_id is None) and (re.search(group_indicator, phrase) is not None):
                # these phrases are not appropriate to return when it's a personal chat
                continue
            for i in range(2):
                phrase = re.sub("random_name", self.rooms[room_index].users[np.random.randint(
                    len(self.rooms[room_index].users))].display_name, phrase, count=1)
            phrase = re.sub("random_past_msg", self.rooms[room_index].messages_list[np.random.randint(
                len(self.rooms[room_index].messages_list))], phrase)
            phrase = re.sub("your_name", name, phrase)
            return_list.append(phrase)
        return return_list

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
        self.print_debug("テキストメッセージを受信!")
        self.all_unlogged_messages.append(text)
        i = self.identify(user_id, group_id)
        rep_text = "エラー"
        if i >= 0:
            self.rooms[i].receive_text(user_id, text)
            phrase_list = self.decode(self.nn.feedForward(text))
            substituted_list = self.substitute(phrase_list, user_id, group_id)
            rep_text = substituted_list[np.random.randint(
                len(substituted_list))]
            self.rooms[i].send_text(rep_text)
        return TextSendMessage(text=rep_text)

    def receive_media(self, user_id, group_id, r, ext):
        room_num = self.identify(user_id, group_id)
        text = "何か面白そうなもの送ってくれたね、でも今は返信できない><"
        if ext == '.jpg':
            # received image
            self.rooms[room_num].receive_img(user_id, r)
            text = "画像送ってくれたね、でも今は画像で返信できない><"
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
        self.print_debug("既に保存されているユーザーなのか、特定中…\nUser ID:\t" +
                         str(user_id) + "\nGroup ID\t" + str(group_id))
        if group_id is None:
            self.print_debug("個チャですね。")
            for i in range(len(self.rooms)):
                if self.rooms[i].id == user_id:
                    # the id of a room is the user_id, if it's a solo chat room
                    self.print_debug("ユーザーを、ルームID " + str(i) + "で発見。")
                    return i
            self.print_debug("新しい個チャですね!")
            return -1
        else:
            self.print_debug("トークルームか、グルチャですね。")
            for i in range(len(self.rooms)):
                if self.rooms[i].id == group_id:
                    self.print_debug("ルームを特定。このユーザーが既にそのグループで発言したか、特定中…")
                    if self.rooms[i].identify(user_id) >= 0:
                        self.print_debug("ユーザーが過去にこのルームで発言していたことを発見！")
                        return i
                    self.print_debug("このルームにおいて、新規ユーザーですね。")
                    return -1
            self.print_debug("新しいルームですね！")
            return -1

    def add_room_or_user(self, profile, group_id=None):
        self.print_debug("新規ユーザーを追加中…")
        if group_id is None:
            self.print_debug("個チャですね")
            self.rooms.append(Room(profile.user_id))
            self.rooms[len(self.rooms) - 1].add_user(profile)
        else:
            self.print_debug("新しいルーム、または既に記録されているルームの中での新しいユーザーですね！")
            for room in self.rooms:
                if room.id == group_id:
                    self.print_debug("または既に記録されているルームの中での新しいユーザーですね")
                    room.add_user(profile)
                    return
            self.print_debug("新しいルームですね!")
            self.rooms.append(Room(group_id))
            self.rooms[len(self.rooms) - 1].add_user(profile)

    def print_debug(self, text):
        if self.debug:
            print("Logic\t", text)

    def make_paths(self):
        '''
        make the paths required for logging.
        '''
        self.print_debug("making log directory...")
        # make directories if they don't exist yet.
        if not os.path.exists("log"):
            # https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
            os.makedirs("log")
        if not os.path.exists("log/all_received_messages"):
            os.makedirs("log/all_received_messages")

    def save_log(self):
        '''
        saves logs of conversations.
        '''
        self.print_debug("ログを保存中…")
        self.make_paths()
        filepath = "log/all_received_messages/" + self.get_date() + ".csv"
        self.print_debug("saving all received messages to " + filepath)
        self.filesmanager.save_list_to_csv(
            self.all_unlogged_messages, filepath, append=True)
        self.all_unlogged_messages = []  # reset to empty
        for room in self.rooms:
            room.log(self.get_date())
        self.print_debug("ログ保存が終了!")

    def get_date(self):
        cur_time = time.localtime()
        return str(cur_time.tm_year) + "_" + str(cur_time.tm_mon) + "_" + str(cur_time.tm_mday)


class Room:
    '''
    Consolidates information about a talk room.
    Mostly just for logging purposes.
    '''

    def __init__(self, id, solo=True, debug=True):
        '''
        If one-on-one talk, id is the user id.
        in other cases, id is the group/chatroom id.
        '''
        self.id = id
        self.debug = debug
        self.users = []
        # saves logs for humans to read later.
        self.messages_forhumans_unlogged = []
        self.messages_list = []  # saves all the received messages.
        # saves the received messages that weren't yet logged.
        self.messages_list_unlogged = []
        self.filesmanager = FilesManager()
        self.initialize_messages()
        self.initialize_users()
        self.make_paths()

    def initialize_users(self):
        '''
        tries to load the csv with the data about members of this room.
        '''
        path = "log/"+self.id+"/members.csv"
        self.print_debug("loading previously saved users stored in " + path)
        users_list = self.filesmanager.load_csv_to_list(path)
        if users_list is None:
            self.print_debug("file not found.")
            return
        for user in users_list:
            if self.identify(user[0]) >= 0:
                continue
            self.print_debug("saving user "+str(user))
            self.users.append(User(None, user[0], user[1], user[2], user[3]))

    def make_paths(self):
        '''
        makes paths required to log stuff (if it's not already there.)
        '''
        self.print_debug("making paths for room " + str(self.id))
        if not os.path.exists("log/"+str(self.id)):
            os.makedirs("log/"+str(self.id))
        if not os.path.exists("log/"+str(self.id)+"/profile_img"):
            os.makedirs("log/"+str(self.id)+"/profile_img")
        if not os.path.exists("log/"+str(self.id)+"/img"):
            os.makedirs("log/"+str(self.id)+"/img")

    def print_debug(self, msg):
        if self.debug:
            print("room ", self.id, "\t", msg)

    def log(self, date):
        self.print_debug("logging info for room " + str(self.id))
        filepath = "log/"+str(self.id)+"/"+date+".csv"
        self.print_debug("saving log for humans to " + filepath)
        self.filesmanager.save_list_to_csv(
            self.messages_forhumans_unlogged, filepath, append=True)
        self.messages_forhumans_unlogged = []
        filepath = "log/"+str(self.id)+"/all_received_messages.csv"
        self.print_debug(
            "saving log for machine to load later, to " + filepath)
        self.filesmanager.save_list_to_csv(
            self.messages_list_unlogged, filepath, append=True)
        self.messages_list_unlogged = []
        user_data = []
        for user in self.users:
            user_data.append([user.user_id, user.display_name,
                              user.picture_url, user.status_message])
        filepath = "log/"+str(self.id)+"/members.csv"
        self.print_debug("saving user infos to "+filepath)
        self.filesmanager.save_list_to_csv(user_data, filepath)
        self.print_debug("logging finished for room "+str(self.id))

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
        if self.identify(profile.user_id) >= 0:
            return
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
        self.messages_forhumans_unlogged.append([name, self.get_time(), text])
        if text[-3:] == "jpg" or text[-3:] == "mp4" or text[-3:] == "m4a":
            return
        self.messages_list.append(text)
        self.messages_list_unlogged.append(text)

    def receive_img(self, user_id, r):
        self.print_debug("received image.")
        filename = str(int(time.time())) + ".jpg"
        with open("log/" + str(self.id) + "/img/" + filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        self.receive_text(user_id, filename)

    def send_text(self, text):
        '''
        when the bot sends a text message to the user
        '''
        self.messages_forhumans_unlogged.append(
            ["BOT", self.get_time(),  text])

    def initialize_messages(self):
        '''
        looks for a csv file with previously received messages, and loads it into messages_list if it's found.
        '''
        print("loading previous logs")
        tmp_list = self.filesmanager.load_csv_to_list(
            "log/" + self.id + "/all_received_messages.csv")
        if tmp_list is None:
            self.messages_list = []
        else:
            self.messages_list = tmp_list
        print("loaded log: ", self.messages_list)

    def get_time(self):
        cur_time = time.localtime()
        return (str(cur_time.tm_mon) + "月" + str(cur_time.tm_mday)
                + "日" + str(cur_time.tm_hour) + "時" + str(cur_time.tm_min)
                + "分")


class User:
    def __init__(self, profile, user_id=None, display_name=None, picture_url=None, status_message=None):
        '''
        get the profile with
        profile = line_bot_api.get_profile(user_id)
        '''
        if profile is not None:
            self.user_id = profile.user_id
            self.display_name = profile.display_name
            self.picture_url = profile.picture_url
            self.status_message = profile.status_message
        else:
            self.user_id = user_id
            self.display_name = display_name
            self.picture_url = picture_url
            self.status_message = status_message
