import json
import os
import time
import traceback

import logging
from datetime import datetime, timedelta

import praw
import requests
from bitcoinrpc.authproxy import AuthServiceProxy

from config import rpc_config, bot_config, url_get_value
import user_function

# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# logger = logging.getLogger('prawcore')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(handler)

reddit = praw.Reddit('sodogetiptest')
rpc = AuthServiceProxy("http://%s:%s@%s:%s" % (
    rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
    rpc_config['doge_rpc_port']))

linkRegister = '[register](http://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Bregister&message=%2Bregister)'


def main():
    # create file if not exist (user storage)
    if not os.path.exists(bot_config['user_file']):
        print "create an empty user file"
        data = {}
        with open(bot_config['user_file'], 'w+') as f:
            json.dump(data, f)

    # create file if not exist (tip unregistered user )
    if not os.path.exists(bot_config['unregistered_tip_user']):
        print "create an empty unregistered tip user file"
        data = {}
        with open(bot_config['unregistered_tip_user'], 'w+') as f:
            json.dump(data, f)

    for msg in reddit.inbox.unread(limit=None):

        print str(msg) + ' - ' + msg.author.name + ' sub : ' + msg.subject
        msg_body = msg.body.strip()
        msg_subject = msg.subject.strip()
        split_message = msg_body.split()

        if msg_body == '+register' and msg_subject == '+register':
            mark_msg_read(msg)
            if not user_function.user_exist(msg.author.name):
                register_user(msg)
                # check if user have pending tips
                have_pending_tips = user_function.get_user_pending_tip(msg.author.name)
                if have_pending_tips != False:
                    # check if it's not too old & replay tipping
                    limit_date = datetime.now() - timedelta(days=3)
                    if (datetime.datetime.strptime(have_pending_tips['time']) < limit_date):
                        # Todo : after restructuration of code
                        print "replay tipping"
            else:
                print msg.author.name + ' are already registered '
                msg.reply('You are already registered ')

        elif msg_body == '+info' and msg_subject == '+info':
            mark_msg_read(msg)
            if user_function.user_exist(msg.author.name):
                user_function.get_user_info(msg)
            else:
                msg.reply('You need %s before' % linkRegister)

        elif msg_body == '+balance' and msg_subject == '+balance':
            mark_msg_read(msg)
            if user_function.user_exist(msg.author.name):
                balance = get_user_balance(msg.author.name)
                print('user %s balance = %s' % (msg.author.name, balance))
                value_usd = get_coin_value(balance)
                msg.reply('Your balance : ' + str(balance) + ' ( ' + str(value_usd) + '$ ) ')
            else:
                print('user %s not registered ' % (msg.author.name))
                msg.reply('You need %s before' % linkRegister)

        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
            mark_msg_read(msg)
            if user_function.user_exist(msg.author.name):
                sender_address = user_function.get_user_address(msg.author.name)
                amount = split_message[1]
                if check_amount_valid(amount):
                    receiver_address = split_message[4]
                    try:
                        send_to(sender_address, receiver_address, amount, True)
                    except:
                        traceback.print_exc()
                    msg.reply('Withdraw : ' + str(amount) + ' to ' + receiver_address)
                else:
                    print('You must use valid amount')
                    msg.reply('You must use valid amount')
            else:
                msg.reply('You need %s before' % linkRegister)

        elif split_message.count('+/u/sodogetiptest'):
            print('An user mention detected ')
            mark_msg_read(msg)
            tip_index = split_message.index('+/u/sodogetiptest')

            if split_message[tip_index] == '+/u/sodogetiptest' and split_message[tip_index + 2] == 'doge':
                amount = split_message[tip_index + 1]

                if check_amount_valid(amount):
                    parent_comment = msg.parent()
                    if user_function.user_exist(msg.author.name):
                        # check user have address before tip
                        if user_function.user_exist(parent_comment.author.name):
                            if int(amount) >= get_user_balance(msg.author.name):
                                print('user %s not have enough to tip this amount (%s), balance = %s' % (
                                    msg.author.name, amount, get_user_balance(msg.author.name)))
                                msg.reply('+/u/%s your balance is too low for this tip ' % msg.author.name)
                            else:
                                print '%s tip %s to %s' % (msg.author.name, str(amount), parent_comment.author.name)
                                msg.reply('+/u/%s tip %s to %s' % (msg.author.name, str(amount),
                                                                   parent_comment.author.name))
                                tip_user(msg.author.name, parent_comment.author.name, amount)
                        else:
                            user_function.save_unregistered_tip(msg.author.name, parent_comment.author.name, amount)
                            print('user %s not registered' % parent_comment.author.name)
                            msg.reply(
                                '+/u/%s need %s before can be tipped (tip saved during 3 day)' % (
                                    parent_comment.author.name, linkRegister)
                            )
                    else:
                        msg.reply('You need %s before' % linkRegister)
                else:
                    print('You must use valid amount')
                    msg.reply('You must use valid amount')

        else:
            mark_msg_read(msg)
            # msg.reply('Currently not supported')
            print 'Currently not supported'

        # to not explode rate limit :)
        print 'Make an pause !'
        time.sleep(3)


def check_amount_valid(amount):
    if amount.isdigit() and amount >= 1:
        return True
    else:
        return False


def register_user(msg):
    address = rpc.getnewaddress()
    msg.reply(msg.author.name + ' registered, your address is ' + address)
    user_function.add_user(msg.author.name, address)


def mark_msg_read(msg):
    unread_messages = []
    unread_messages.append(msg)
    reddit.inbox.mark_read(unread_messages)


def get_user_balance(user):
    pending_tips = []
    unspent_amounts = []

    address = user_function.get_user_address(user)
    list_unspent = rpc.listunspent(0, 99999999999, [address])
    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])

    # check if user have pending tips
    list_tip_unregistered = user_function.get_unregistered_tip()
    for tip in list_tip_unregistered.values():
        if tip['sender']:
            pending_tips.append(int(tip['amount']))

    return int(sum(unspent_amounts) - sum(pending_tips))


def tip_user(sender_user, receiver_user, amount_tip):
    sender_address = user_function.get_user_address(sender_user)
    receiver_address = user_function.get_user_address(receiver_user)
    try:
        send_to(sender_address, receiver_address, amount_tip)
    except:
        traceback.print_exc()


def send_to(sender_address, receiver_address, amount, take_fee_on_amount=False):
    print "send " + amount + " to " + receiver_address + " from " + sender_address

    list_unspent = rpc.listunspent(0, 99999999999, [sender_address])

    unspent_list = []
    unspent_vout = []
    unspent_amounts = []

    for i in range(0, len(list_unspent), 1):
        unspent_list.append(list_unspent[i]['txid'])
        unspent_vout.append(list_unspent[i]['vout'])
        unspent_amounts.append(list_unspent[i]['amount'])
        if sum(unspent_amounts) > amount:
            break

    print "sum of unspend :" + str(sum(unspent_amounts))

    raw_inputs = []
    for i in range(0, len(list_unspent), 1):
        tx = {
            "txid": str(list_unspent[i]['txid']),
            "vout": list_unspent[i]['vout']
        }
        raw_inputs.append(tx)
    print "raw input :"
    print raw_inputs

    fee = calculate_fee(raw_inputs, None)
    print "fee : " + str(fee)
    fee = 1

    if take_fee_on_amount:
        amount = (int(amount) - int(fee))

    return_amount = int(sum(unspent_amounts)) - int(amount) - int(fee)

    print "return_amount : " + str(return_amount)

    if return_amount < 1:
        raw_addresses = {receiver_address: int(amount)}
    else:
        raw_addresses = {receiver_address: int(amount), sender_address: return_amount}

    print "raw addresses :"
    print raw_addresses

    raw_tx = rpc.createrawtransaction(raw_inputs, raw_addresses)
    print "raw tx :"
    print(raw_tx)

    print 'send ' + str(amount) + ' Doge form ' + receiver_address + ' to ' + receiver_address

    signed = rpc.signrawtransaction(raw_tx)
    send = rpc.sendrawtransaction(signed['hex'])


def calculate_fee(raw_inputs, raw_addresses):
    nb_input = len(raw_inputs)
    # nb_out = len(raw_addresses)
    nb_out = 2
    fee = nb_input * 180 + nb_out * 34 + 10
    return fee


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


while True:
    try:
        main()
    except:
        traceback.print_exc()
        print('Resuming in 30sec...')
        time.sleep(30)
