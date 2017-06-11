import datetime
from tinydb import TinyDB

import bot_logger
from config import DATA_PATH, bot_config


# return all history of users
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

