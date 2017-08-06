import json
import os
import traceback

import requests
from tinydb import TinyDB

import bot_logger
import config
from config import url_get_value


def create_user_storage():
    if not os.path.exists(config.user_file):
        bot_logger.logger.info("create an empty user file")
        data = {}
        with open(config.user_file, 'w+') as f:
            json.dump(data, f)


def create_unregistered_tip_storage():
    if not os.path.exists(config.unregistered_tip_user):
        bot_logger.logger.info("create an empty unregistered tip user file")
        db = TinyDB(config.unregistered_tip_user)
        db.close()


def get_coin_value(balance, currency=None, format=2):
    str_format = str("{0:." + str(format) + "f}")

    try:
        jc_currency = requests.get(url_get_value['cryptonator']).json()
        coin_val = xpath_get(jc_currency, "/ticker/price")
    except:
        try:
            jc_currency = requests.get(url_get_value['coincap']).json()
            coin_val = xpath_get(jc_currency, "/usdPrice")
        except:
            try:
                jc_currency = requests.get(url_get_value['cryptocompare']).json()
                coin_val = xpath_get(jc_currency, "/Data/O/Price")
            except:
                traceback.print_exc()
                return 0

    bot_logger.logger.info('value is $%s' % str(coin_val))
    usd_currency = float(str_format.format(int(balance) * float(coin_val)))
    return usd_currency


def check_amount_valid(amount):
    try:
        if (float(amount)) >= 1:
            # print('such amount : '+str(amount))
            return True
        else:
            return False
    except (UnicodeEncodeError, ValueError):
        return False


def xpath_get(mydict, path):
    elem = mydict
    try:
        for x in path.strip("/").split("/"):
            try:
                x = int(x)
                elem = elem[x]
            except ValueError:
                elem = elem.get(x)
    except:
        pass

    return elem


def mark_msg_read(reddit, msg):
    unread_messages = [msg]
    reddit.inbox.mark_read(unread_messages)
