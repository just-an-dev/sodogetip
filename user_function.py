import json

from tinydb import TinyDB, Query

import bot_logger
import config


# read file
def get_users():
    with open(config.user_file, 'r') as f:
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
    with open(config.user_file, 'w') as f:
        data[user] = address
        json.dump(data, f)


def get_unregistered_tip():
    db = TinyDB(config.unregistered_tip_user)
    data = db.all()
    db.close()
    return data


def save_unregistered_tip(tip):
    bot_logger.logger.info("Save tip form %s to %s " % (tip.sender.username, tip.receiver.username))
    db = TinyDB(config.unregistered_tip_user)
    db.insert({
        'id': tip.id,
        'amount': tip.amount,
        'receiver': tip.receiver.username,
        'sender': tip.sender.username,
        'message_fullname': tip.message_fullname,
        'time': tip.time,
    })
    db.close()


def remove_pending_tip(id_tip):
    db = TinyDB(config.unregistered_tip_user)
    tip = Query()
    db.remove(tip.id == id_tip)
    db.close()


def get_balance_unregistered_tip(user):
    pending_tips = []

    list_tip_unregistered = get_unregistered_tip()
    if list_tip_unregistered:
        for tip in list_tip_unregistered:
            if tip['sender'] == user:
                pending_tips.append(int(tip['amount']))

    return int(sum(pending_tips))
