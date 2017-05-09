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
        msgbody = msg.body
        msgsubject = msg.subject
        dict = user_function.get_users()
        splitmessage = msgbody.split()
        if msgbody == '+register' and msgsubject == '+register':
            mark_msg_read(msg)
            if msg.author.name not in dict:
                register_user(msg)
            else:
                print msg.author.name + ' are already registered '
                msg.reply('You are already registered ')
        elif msgbody == '+info' and msgsubject == '+info':
            mark_msg_read(msg)
            if msg.author.name in dict:
                user_function.get_user_info(msg)
            else:
                msg.reply('You need register before')
        elif msgbody == '+balance' and msgsubject == '+balance':
            mark_msg_read(msg)
            if msg.author.name in dict:
                balance = get_user_balance(msg.author.name)
                msg.reply('Your balance : ' + str(balance))

            else:
                msg.reply('You need register before')
        elif splitmessage.count('+withdraw') and msgsubject == '+withdraw':
            mark_msg_read(msg)
            if msg.author.name in dict:
                sender_address = user_function.get_user_address(msg.author.name)
                amount = splitmessage[1]
                receiver_address = splitmessage[4]
                send_to(sender_address, receiver_address, amount)

                msg.reply('Withdraw : ' + str(amount) + ' to ' + receiver_address)
            else:
                msg.reply('You need register before')
        elif splitmessage.count('+/u/sodogetiptest'):
            print('An user mention detected ')
            mark_msg_read(msg)
            tipindex = splitmessage.index('+/u/sodogetiptest')

            if splitmessage[tipindex] == '+/u/sodogetiptest' and splitmessage[tipindex + 2] == 'doge':
                try:
                    amount = splitmessage[tipindex + 1]
                except:
                    continue
                parent_comment = msg.parent()
                msg.reply('+/u/' + msg.author.name + ' tip ' + str(amount) + ' to ' + parent_comment.author.name)
                print msg.author.name + ' tip ' + str(amount) + ' to ' + parent_comment.author.name
                if user_function.user_exist(msg.author.name):
                    # check user have address before tip
                    if parent_comment.author.name in dict:
                        tip_user(msg.author.name, parent_comment.author.name, amount)
                    else:
                        msg.reply('+/u/' + parent_comment.author.name + ' need register before can be tipped')
                else:
                    msg.reply('You need register before')
        else:
            mark_msg_read(msg)
            msg.reply('Currently not supported')
            print 'Currently not supported'
        # to not explode rate limit :)
        print 'Make an pause !'
        time.sleep(3)


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

    return_amount = float(sum(unspent_amounts)) - float(amount) - float(fee)
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
