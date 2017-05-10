import json
import os
import time
import traceback

import logging
import praw
from bitcoinrpc.authproxy import AuthServiceProxy

from config import rpc_config, bot_config
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


def main():
    # create file fi not exist
    if not os.path.exists(bot_config['user_file']):
        print "create an empty file"
        data = {}
        with open(bot_config['user_file'], 'w+') as f:
            json.dump(data, f)

    for msg in reddit.inbox.unread(limit=None):

        print str(msg) + ' - ' + msg.author.name + ' sub : ' + msg.subject
        msg_body = msg.body
        msg_subject = msg.subject
        split_message = msg_body.split()

        if msg_body == '+register' and msg_subject == '+register':
            mark_msg_read(msg)
            if not user_function.user_exist(msg.author.name):
                register_user(msg)
            else:
                print msg.author.name + ' are already registered '
                msg.reply('You are already registered ')

        elif msg_body == '+info' and msg_subject == '+info':
            mark_msg_read(msg)
            if user_function.user_exist(msg.author.name):
                user_function.get_user_info(msg)
            else:
                msg.reply('You need register before')

        elif msg_body == '+balance' and msg_subject == '+balance':
            mark_msg_read(msg)
            if user_function.user_exist(msg.author.name):
                balance = get_user_balance(msg.author.name)
                msg.reply('Your balance : ' + str(balance))
            else:
                msg.reply('You need register before')

        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
            mark_msg_read(msg)
            if user_function.user_exist(msg.author.name):
                sender_address = user_function.get_user_address(msg.author.name)
                amount = split_message[1]
                if check_amount_valid(amount):
                    receiver_address = split_message[4]
                    send_to(sender_address, receiver_address, amount)
                    msg.reply('Withdraw : ' + str(amount) + ' to ' + receiver_address)
                else:
                    print('You must use valid amount')
                    msg.reply('You must use valid amount')
            else:
                msg.reply('You need register before')

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
                            if get_user_balance(msg.author.name) <= amount:
                                print('user ' + msg.author.name + ' not have enough to tip this amount (%s), balance = %s'% (amount, get_user_balance(msg.author.name)) )
                                msg.reply('+/u/' + msg.author.name + ' your balance is too low for this tip ')
                            else:
                                print msg.author.name + ' tip ' + str(amount) + ' to ' + parent_comment.author.name
                                msg.reply(
                                    '+/u/' + msg.author.name + ' tip ' + str(amount) + ' to ' + parent_comment.author.name)
                                tip_user(msg.author.name, parent_comment.author.name, amount)
                        else:
                            print('user '+ parent_comment.author.name + ' not registered')
                            msg.reply('+/u/' + parent_comment.author.name + ' need register before can be tipped')
                    else:
                        msg.reply('You need register before')
                else:
                    print('You must use valid amount')
                    msg.reply('You must use valid amount')

        else:
            mark_msg_read(msg)
            msg.reply('Currently not supported')
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
    address = user_function.get_user_address(user)
    list_unspent = rpc.listunspent(0, 99999999999, [address])
    unspent_amounts = []
    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])

    return sum(unspent_amounts)


def tip_user(sender_user, receiver_user, amount_tip):
    sender_address = user_function.get_user_address(sender_user)
    receiver_address = user_function.get_user_address(receiver_user)
    send_to(sender_address, receiver_address, amount_tip)


def send_to(sender_address, receiver_address, amount):
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

    # print(unspentlist)
    # print(unspentvout)
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

    return_amount = int(sum(unspent_amounts)) - int(amount) - int(fee)
    print "return_amount : " + str(return_amount)

    raw_addresses = {receiver_address: int(amount), sender_address: return_amount}

    print "raw addresses :"
    print raw_addresses

    raw_tx = rpc.createrawtransaction(raw_inputs, raw_addresses)
    print "raw tx :"
    print(raw_tx)

    print 'send ' + amount + ' Doge form ' + receiver_address + ' to ' + receiver_address

    signed = rpc.signrawtransaction(raw_tx)
    send = rpc.sendrawtransaction(signed['hex'])


def calculate_fee(raw_inputs, raw_addresses):
    nb_input = len(raw_inputs)
    # nb_out = len(raw_addresses)
    nb_out = 2
    fee = nb_input * 180 + nb_out * 34 + 10
    return fee


while True:
    try:
        main()
    except:
        traceback.print_exc()
        print('Resuming in 30sec...')
        time.sleep(30)
