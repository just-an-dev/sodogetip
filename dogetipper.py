import os
import time
import traceback

import praw
from bitcoinrpc.authproxy import AuthServiceProxy

import bot_command
import bot_logger
import utils
from config import rpc_config, bot_config, DATA_PATH

reddit = praw.Reddit('sodogetiptest')
rpc = AuthServiceProxy("http://%s:%s@%s:%s" % (
    rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
    rpc_config['doge_rpc_port']))


def main():
    if not os.path.exists(DATA_PATH + bot_config['user_history_path']):
        os.makedirs(DATA_PATH + bot_config['user_history_path'])

    # create file if not exist (user storage)
    utils.create_user_storage()

    # create file if not exist (tip unregistered user )
    utils.create_unregistered_tip_storage()

    for msg in reddit.inbox.unread(limit=None):

        bot_logger.logger.info("%s - %s sub : %s" % (str(msg), msg.author.name, msg.subject))
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

        elif msg_body == '+history' or msg_subject == '+history':
            mark_msg_read(msg)
            bot_command.history_user(msg)

        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
            mark_msg_read(msg)
            bot_command.withdraw_user(rpc, msg)

        elif split_message.count('+/u/sodogetiptest'):
            mark_msg_read(msg)
            bot_command.tip_user(rpc, msg)

        else:
            mark_msg_read(msg)
            # msg.reply('Currently not supported')
            bot_logger.logger.info('Currently not supported')

        # to not explode rate limit :)
        bot_logger.logger.info('Make an pause !')
        time.sleep(3)
        bot_logger.logger.info('Make clean of unregistered tips')
        bot_command.replay_remove_pending_tip(rpc)

def mark_msg_read(msg):
    unread_messages = []
    unread_messages.append(msg)
    reddit.inbox.mark_read(unread_messages)


bot_logger.logger.info("Bot Started !!")
while True:
    try:
        main()
    except:
        traceback.print_exc()
        bot_logger.logger.error('Resuming in 30sec...')
        time.sleep(30)
