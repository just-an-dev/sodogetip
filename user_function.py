import json

from tinydb import TinyDB, Query

import bot_logger
import config


# read file
# Todo : to remove after migration of user base
def get_users_old():
    with open(config.DATA_PATH + 'user_files.json', 'r') as f:
        try:
            data = json.load(f)
        except ValueError:
            bot_logger.logger.warning("Error on read user file")
            data = {}
        return data


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


def save_multisig(username, multisig):
    db = TinyDB(DATA_PATH + bot_config['multisig_user'])
    db.insert({
        'user': username,
        'address': multisig['address'],
        'redeemscript': multisig['redeemScript'],
        'type': "1of2",
        'enabled': True,
    })
    db.close()
