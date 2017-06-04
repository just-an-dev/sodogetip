import datetime
import json
import random
from tinydb import TinyDB, Query

import bot_logger
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
    user_list = get_users()
    return user_list[user]


def user_exist(user):
    user_list = get_users()
    if user in user_list.keys():
        return True
    else:
        return False


def get_unregistered_tip():
    db = TinyDB(DATA_PATH + bot_config['unregistered_tip_user'])
    data = db.all()
    db.close()
    return data


def save_unregistered_tip(sender, receiver, amount, message_fullname):
    bot_logger.logger.info("Save tip form %s to %s " % (sender, receiver))
    db = TinyDB(DATA_PATH + bot_config['unregistered_tip_user'])
    db.insert({
        'id': random.randint(0, 99999999),
        'amount': amount,
        'receiver': receiver,
        'sender': sender,
        'message_fullname': message_fullname,
        'time': datetime.datetime.now().isoformat(),
    })
    db.close()


def remove_pending_tip(id_tip):
    db = TinyDB(DATA_PATH + bot_config['unregistered_tip_user'])
    tip = Query()
    db.remove(tip.id == id_tip)
    db.close()


def get_user_history(user):
    db = TinyDB(DATA_PATH + bot_config['user_history_path'] + user + '.json')
    data = db.all()
    db.close()
    return data


def add_to_history(user_history, sender, receiver, amount, action, finish=True, tx_id =""):
    bot_logger.logger.info("Save for history user=%s, sender=%s, receiver=%s, amount=%s, action=%s, finish=%s" % (
        user_history, sender, receiver, amount, action, finish))

    db = TinyDB(DATA_PATH + bot_config['user_history_path'] + user_history + '.json')
    db.insert({
        "user": user_history,
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "action": action,
        "finish": finish,
        "tx_id": tx_id,
        'time': datetime.datetime.now().isoformat(),
    })
    db.close()


def get_balance_unregistered_tip(user):
    pending_tips = []

    list_tip_unregistered = get_unregistered_tip()
    if list_tip_unregistered:
        for tip in list_tip_unregistered:
            if tip['sender'] == user:
                pending_tips.append(int(tip['amount']))

    return int(sum(pending_tips))
