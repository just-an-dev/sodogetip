import datetime

from tinydb import TinyDB, Query

import bot_logger
from config import DATA_PATH, bot_config


# return all history of users
def repare_history(user):
    db = TinyDB(DATA_PATH + bot_config['user_history_path'] + user + '.json')
    ver = db.table("version")
    patch = Query()
    data = ver.search(patch.v1 == 'ok')
    if len(data) is 0 and data[0]['v1'] is not 'ok':
        # not patch apply
        def_table = db.table("_default")
        data_histo = def_table.all()
        for row in data_histo:
            if len(row['finish']) == 74 and row['tx_id'] == "":
                # invert the 2 fields
                cur_finish = row['finish']
                db.update({'tx_id': cur_finish}, eids=[row.eid])
                db.update({'finish': True}, eids=[row.eid])
        ver.insert({'v1': 'ok'})
        bot_logger.logger.info('update of history of user %s (ok)' % user)
    db.close()


def get_user_history(user):
    repare_history(user)
    db = TinyDB(DATA_PATH + bot_config['user_history_path'] + user + '.json')
    data = db.all()
    db.close()
    return data


def add_to_history(user_history, sender, receiver, amount, action, finish=True, tx_id=""):
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


def add_to_history_tip(user_history, action, tip):
    bot_logger.logger.info("Save for history user=%s, sender=%s, receiver=%s, amount=%s, action=%s, finish=%s" % (
        user_history, tip.sender.username, tip.receiver.username, tip.amount, action, tip.finish))

    db = TinyDB(DATA_PATH + bot_config['user_history_path'] + user_history + '.json')
    db.insert({
        "user": user_history,
        "id": tip.id,
        "sender": tip.sender.username,
        "receiver": tip.receiver.username,
        "amount": tip.amount,
        "action": action,
        "finish": tip.finish,
        "tx_id": tip.tx_id,
        'time': tip.time,
    })
    db.close()


def update_tip(user_history, tip):
    # update only finish tips
    if tip.tx_id is not None:
        db = TinyDB(DATA_PATH + bot_config['user_history_path'] + user_history + '.json')
        tip_query = Query()
        db.update({'finish': True}, tip_query.id == tip.id)
        db.update({'tx_id': tip.tx_id}, tip_query.id == tip.id)
        db.close()
