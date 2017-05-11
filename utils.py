import json
import os
import traceback

import requests

from config import bot_config, url_get_value


def create_user_storage():
    if not os.path.exists(bot_config['user_file']):
        print "create an empty user file"
        data = {}
        with open(bot_config['user_file'], 'w+') as f:
            json.dump(data, f)


def create_unregistered_tip_storage():
    if not os.path.exists(bot_config['unregistered_tip_user']):
        print "create an empty unregistered tip user file"
        data = {}
        with open(bot_config['unregistered_tip_user'], 'w+') as f:
            json.dump(data, f)


def get_coin_value(balance):
    try:
        c_currency = requests.get(url_get_value['coincap'])
        jc_currency = c_currency.json()
        print('value is $' + str(jc_currency['usdPrice']))
        usd_currency = float(
            "{0:.2f}".format(int(balance) * float(jc_currency['usdPrice'])))
        return usd_currency
    except:
        try:
            c_currency = requests.get(url_get_value['cryptocompare'])
            jc_currency = c_currency.json()
            print('value is $' + str(jc_currency['Data'][0]['Price']))
            usd_currency = float(
                "{0:.2f}".format(
                    int(balance) * float(jc_currency['Data'][0]['Price'])))
            return usd_currency
        except:
            traceback.print_exc()


def check_amount_valid(amount):
    if amount.isdigit() and amount >= 1:
        return True
    else:
        return False
