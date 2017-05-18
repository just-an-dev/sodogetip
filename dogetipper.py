import os
import time
import traceback
from threading import Thread

import praw
from bitcoinrpc.authproxy import AuthServiceProxy

import bot_command
import bot_logger
import crypto
import utils
from config import rpc_config, bot_config, DATA_PATH


class SoDogeTip():
    def __init__(self):
        self.reddit = praw.Reddit('sodogetiptest')
        self.rpc = AuthServiceProxy("http://%s:%s@%s:%s" % (
            rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
            rpc_config['doge_rpc_port']))

    def main(self):
        if not os.path.exists(DATA_PATH + bot_config['user_history_path']):
            os.makedirs(DATA_PATH + bot_config['user_history_path'])

        # create file if not exist (user storage)
        utils.create_user_storage()

        # create file if not exist (tip unregistered user )
        utils.create_unregistered_tip_storage()

        for msg in self.reddit.inbox.unread(limit=None):

            bot_logger.logger.info("%s - %s sub : %s" % (str(msg), msg.author.name, msg.subject))
            msg_body = msg.body.strip()
            msg_subject = msg.subject.strip()
            split_message = msg_body.split()

            if msg_body == '+register' and msg_subject == '+register':
                self.mark_msg_read(msg)
                bot_command.register_user(self.rpc, msg)

            elif msg_body == '+info' and msg_subject == '+info':
                self.mark_msg_read(msg)
                bot_command.info_user(self.rpc, msg)

            elif msg_body == '+balance' or msg_subject == '+balance':
                self.mark_msg_read(msg)
                bot_command.balance_user(self.rpc, msg)

            elif msg_body == '+history' or msg_subject == '+history':
                self.mark_msg_read(msg)
                bot_command.history_user(msg)

            elif split_message.count('+withdraw') and msg_subject == '+withdraw':
                self.mark_msg_read(msg)
                bot_command.withdraw_user(self.rpc, msg)

            elif split_message.count('+/u/sodogetiptest'):
                self.mark_msg_read(msg)
                bot_command.tip_user(self.rpc, msg)

            else:
                self.mark_msg_read(msg)
                # msg.reply('Currently not supported')
                bot_logger.logger.info('Currently not supported')

            # to not explode rate limit :)
            bot_logger.logger.info('Make an pause !')
            time.sleep(3)

    def mark_msg_read(self, msg):
        unread_messages = [msg]
        self.reddit.inbox.mark_read(unread_messages)

    def process_pending_tip(self, msg):
        bot_logger.logger.info('Make clean of unregistered tips')
        bot_command.replay_remove_pending_tip(self.rpc)

    def anti_spamming_tx(self, msg):
        # protect against spam attacks of an address having UTXOs.
        while True:
            bot_logger.logger.info('Make clean of tx')
            # get list of account
            for account in self.list_account:
                list_tx = self.rpc.listunspent(1, 99999999999, [account['address']])
                if len(list_tx) > bot_config['spam_limit']:
                    bot_logger.logger.info('Consolidate %s account !' % account['name'])
                    amount = crypto.get_user_balance(self.rpc, account['name'])
                    crypto.send_to(self.rpc, account['address'], account['address'], amount)
            time.sleep(30)


if __name__ == "__main__":
    bot_logger.logger.info("Bot Started !!")
    while True:
        try:
            Bot = SoDogeTip()
            thread_master = Thread(target=Bot.main)
            thread_pending_tip = Thread(target=Bot.process_pending_tip)
            thread_master.start()
            thread_pending_tip.start()
            thread_master.join()
        except:
            traceback.print_exc()
            bot_logger.logger.error('Resuming in 30sec...')
            time.sleep(30)
