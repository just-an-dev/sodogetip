import json
import os
import time
import traceback

import logging

import praw
from bitcoinrpc.authproxy import AuthServiceProxy

from config import rpc_config, bot_config, url_get_value

import bot_command
import user_function

# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# logger = logging.getLogger('prawcore')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(handler)

import utils

reddit = praw.Reddit('sodogetiptest')
rpc = AuthServiceProxy("http://%s:%s@%s:%s" % (
    rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
    rpc_config['doge_rpc_port']))


def main():
    if not os.path.exists(bot_config['user_history_path']):
        os.makedirs(bot_config['user_history_path'])

    # create file if not exist (user storage)
    utils.create_user_storage()

    # create file if not exist (tip unregistered user )
    utils.create_unregistered_tip_storage()

    for msg in reddit.inbox.unread(limit=None):

        print str(msg) + ' - ' + msg.author.name + ' sub : ' + msg.subject
        msg_body = msg.body.strip()
        msg_subject = msg.subject.strip()
        split_message = msg_body.split()

        if msg_body == '+register' and msg_subject == '+register':
            mark_msg_read(msg)
            bot_command.register_user(rpc, msg)

        elif msg_body == '+info' and msg_subject == '+info':
            mark_msg_read(msg)
            bot_command.info_user(rpc, msg)

        elif msg_body == '+balance' or msg_subject == '+balance':
            mark_msg_read(msg)
            bot_command.balance_user(rpc, msg)

        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
            mark_msg_read(msg)
            bot_command.withdraw_user(rpc, msg)

        elif split_message.count('+/u/sodogetiptest'):
            mark_msg_read(msg)
            bot_command.tip_user(rpc, msg)

        # only for debug
        elif msg_body == '+pending_tips' and msg_subject == '+pending_tips':
            mark_msg_read(msg)
            bot_command.pending_tips(rpc, msg)

        else:
            mark_msg_read(msg)
            # msg.reply('Currently not supported')
            print 'Currently not supported'

        # to not explode rate limit :)
        print 'Make an pause !'
        time.sleep(3)


def mark_msg_read(msg):
    unread_messages = []
    unread_messages.append(msg)
    reddit.inbox.mark_read(unread_messages)


while True:
    try:
        main()
    except:
        traceback.print_exc()
        print('Resuming in 30sec...')
        time.sleep(30)
