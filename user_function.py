import json

from config import bot_config


# read file
def get_users():
    with open(bot_config['user_file'], 'r') as f:
        try:
            data = json.load(f)
        except ValueError:
            print "Error on read user file"
            data = {}
        return data


# save to file:
def add_user(user, address):
    print("Add user " + user + ' ' + address)
    data = get_users()
    with open(bot_config['user_file'], 'w') as f:
        data[user] = address
        json.dump(data, f)


def get_user_info(msg):
    dict = get_users()
    address = dict[msg.author.name]
    msg.reply(msg.author.name + ' your address is ' + address)


def get_user_address(user):
    dict = get_users()
    return dict[user]


def user_exist(user):
    dict = get_users()
    if user in dict.keys():
        return True
    else:
        return False
