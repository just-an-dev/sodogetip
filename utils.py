import json
import os
import traceback

import requests
from tinydb import TinyDB

import bot_logger
from config import bot_config, url_get_value, DATA_PATH


def create_user_storage():
    if not os.path.exists(DATA_PATH + bot_config['user_file']):
        bot_logger.logger.info("create an empty user file")
        data = {}
        with open(DATA_PATH + bot_config['user_file'], 'w+') as f:
            json.dump(data, f)


def create_unregistered_tip_storage():
    if not os.path.exists(DATA_PATH + bot_config['unregistered_tip_user']):
        bot_logger.logger.info("create an empty unregistered tip user file")
        db = TinyDB(DATA_PATH + bot_config['unregistered_tip_user'])
        db.close()


def get_coin_value(balance, format=2):
    try:
        c_currency = requests.get(url_get_value['cryptonator'])
        jc_currency = c_currency.json()
        bot_logger.logger.info('value is $%s' % str(jc_currency['ticker']['price']))
        usd_currency = float(
            str("{0:." + str(format) + "f}").format(
                int(balance) * float(jc_currency['ticker']['price'])))
        return usd_currency
    except:
        try:
            c_currency = requests.get(url_get_value['coincap'])
            jc_currency = c_currency.json()
            bot_logger.logger.info('value is $%s' % str(jc_currency['usdPrice']))
            usd_currency = float(str("{0:." + str(format) + "f}").format(int(balance) * float(jc_currency['usdPrice'])))
            return usd_currency
        except:
            try:
                c_currency = requests.get(url_get_value['cryptocompare'])
                jc_currency = c_currency.json()
                bot_logger.logger.info('value is $%s' % str(jc_currency['Data'][0]['Price']))
                usd_currency = float(str("{0:." + str(format) + "f}").format(
                    int(balance) * float(jc_currency['Data'][0]['Price'])))
                return usd_currency
            except:
                traceback.print_exc()


def check_amount_valid(amount):
    try:
        if (float(amount)) >= 1:
            # print('such amount : '+str(amount))
            return True
        else:
            return False
    except (UnicodeEncodeError, ValueError):
        return False


def mark_msg_read(reddit, msg):
    unread_messages = [msg]
    reddit.inbox.mark_read(unread_messages)
