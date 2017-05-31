import json

import datetime
import random

import bot_logger
import crypto
import lang
import utils
from config import bot_config, DATA_PATH


# read file
def get_users():
    with open(DATA_PATH + bot_config['user_file'], 'r') as f:
        try:
            data = json.load(f)
        except ValueError:
            bot_logger.logger.warning("Error on read user file")
            data = {}
        return data


# save to file:
def add_user(user, address):
    bot_logger.logger.info("Add user " + user + ' ' + address)
    data = get_users()
    with open(DATA_PATH + bot_config['user_file'], 'w') as f:
        data[user] = address
        json.dump(data, f)


def get_user_address(user):
    dict = get_users()
    return dict[user]


def user_exist(user):
    dict = get_users()
    if user in dict.keys():
        return True
    else:
        return False


def get_unregistered_tip():
    with open(DATA_PATH + bot_config['unregistered_tip_user'], 'r') as f:
        try:
            data = json.load(f)
        except ValueError:
            bot_logger.logger.warning("Error on read unregistered tip user file")
            data = []
        return data


def save_unregistered_tip(sender, receiver, amount, messagefullname):
    bot_logger.logger.info("Save tip form %s to %s " % (sender, receiver))
    data = get_unregistered_tip()
    with open(DATA_PATH + bot_config['unregistered_tip_user'], 'w') as f:
        data.append({
            'id': random.randint(0, 99999999),
            'amount': amount,
            'receiver': receiver,
            'sender': sender,
            'message_fullname': messagefullname,
            'time': datetime.datetime.now().isoformat(),
        })
        json.dump(data, f)


def remove_pending_tip(id):
    unregistered_tip = get_unregistered_tip()
    for key, tip in enumerate(unregistered_tip):
        if int(tip['id']) == int(id):
            del unregistered_tip[key]
    with open(DATA_PATH + bot_config['unregistered_tip_user'], 'w+') as f:
        json.dump(unregistered_tip, f)


def get_user_history(user):
    try:
        with open(DATA_PATH + bot_config['user_history_path'] + user + '.json', 'r') as f:
            try:
                data = json.load(f)
            except ValueError:
                bot_logger.logger.warning("Error on read user file history")
                data = []
    except IOError:
        bot_logger.logger.warning("Error on read user file history")
        data = []
    return data


def add_to_history(user_history, sender, receiver, amount, action, finish=True):
    bot_logger.logger.info("Save for history user=%s, sender=%s, receiver=%s, amount=%s, action=%s, finish=%s" % (
        user_history, sender, receiver, amount, action, finish))
    data = get_user_history(user_history)
    with open(DATA_PATH + bot_config['user_history_path'] + user_history + '.json', 'w+') as f:
        data.append({
            "user": user_history, "sender": sender, "receiver": receiver, "amount": amount, "action": action,
            "finish": finish,
            'time': datetime.datetime.now().isoformat(),
        })
        json.dump(data, f)


def get_balance_unregistered_tip(user):
    pending_tips = []

    list_tip_unregistered = get_unregistered_tip()
    if list_tip_unregistered:
        for tip in list_tip_unregistered:
            if tip['sender'] == user:
                pending_tips.append(int(tip['amount']))

    return int(sum(pending_tips))