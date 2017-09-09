import datetime
import random

from tinydb import TinyDB, Query

import bot_logger
import config
import models


def get_user_history(user):
    db = TinyDB(config.history_path + user + '.json')
    data = db.all()
    db.close()
    return data


def add_to_history(user_history, sender, receiver, amount, action, finish=False, tx_id="", tip_id=""):
    # convert object to string of name if necessary
    if type(user_history) is models.User:
        user_history = user_history.username

    if tip_id == "":
        tip_id = random.randint(0, 99999999)

    bot_logger.logger.info("Save for history user=%s, sender=%s, receiver=%s, amount=%s, action=%s, finish=%s" % (
        user_history, sender, receiver, amount, action, finish))

    db = TinyDB(config.history_path + user_history + '.json')
    db.insert({
        "id": tip_id,
        "user": user_history,
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "action": action,
        "finish": finish,
        "status": "",
        "tx_id": tx_id,
        'time': datetime.datetime.now().isoformat(),
    })
    db.close()


def add_to_history_tip(user_history, action, tip):
    # convert object to string of name if necessary
    if type(user_history) is models.User:
        user_history = user_history.username

    bot_logger.logger.info("Save for history user=%s, sender=%s, receiver=%s, amount=%s, action=%s, finish=%s" % (
        user_history, tip.sender.username, tip.receiver.username, tip.amount, action, tip.finish))

    db = TinyDB(config.history_path + user_history + '.json')
    db.insert({
        "user": user_history,
        "id": tip.id,
        "sender": tip.sender.username,
        "receiver": tip.receiver.username,
        "amount": tip.amount,
        "action": action,
        "finish": tip.finish,
        "status": tip.status,
        "tx_id": tip.tx_id,
        'time': tip.time,
    })
    db.close()


def update_tip(user_history, tip):
    # convert object to string of name if necessary
    if type(user_history) is models.User:
        user_history = user_history.username

    # update only finish tips
    bot_logger.logger.info("update history for user=%s, tip.tx_id=%s" % (user_history, tip.tx_id))
    if tip.id is not None:
        bot_logger.logger.info("update history for user=%s, tip.id=%s" % (user_history, tip.id))

        db = TinyDB(config.history_path + user_history + '.json')
        tip_query = Query()
        db.update({'finish': tip.finish}, tip_query.id == tip.id)
        db.update({'tx_id': tip.tx_id}, tip_query.id == tip.id)
        db.update({'status': tip.status}, tip_query.id == tip.id)
        db.close()
    else:
        bot_logger.logger.warn("update history fail user=%s, tip.id=%s" % (user_history, tip.id))


def update_withdraw(user_history, status, tx_id, tip_id):
    # convert object to string of name if necessary
    if type(user_history) is models.User:
        user_history = user_history.username

    # update only finish tips
    if tip_id is not None:
        bot_logger.logger.info("update history for user=%s, tip.id=%s" % (user_history, tip_id))

        db = TinyDB(config.history_path + user_history + '.json')
        tip_query = Query()
        db.update({'finish': status}, tip_query.id == tip_id)
        db.update({'tx_id': tx_id}, tip_query.id == tip_id)
        db.update({'status': "finish"}, tip_query.id == tip_id)
        db.close()
    else:
        bot_logger.logger.warn("update history fail user=%s, tip.id=%s" % (user_history, tip_id))
