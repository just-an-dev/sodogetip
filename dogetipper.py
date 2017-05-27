import os
import time
import traceback
from threading import Thread

import praw
from bitcoinrpc.authproxy import AuthServiceProxy
from praw.models import Message, Comment

import bot_command
import bot_logger
import crypto
import lang
import user_function
import utils
from config import rpc_config, bot_config, DATA_PATH


class SoDogeTip():
    def __init__(self):
        self.reddit = praw.Reddit('sodogetiptest')

        self.rpc_main = AuthServiceProxy("http://%s:%s@%s:%s" % (
            rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
            rpc_config['doge_rpc_port']), timeout=120)

        self.rpc_antispam = AuthServiceProxy("http://%s:%s@%s:%s" % (
            rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
            rpc_config['doge_rpc_port']), timeout=120)

    def main(self):
        bot_logger.logger.info('Main Bot loop !')
        while True:
            try:
                if not os.path.exists(DATA_PATH + bot_config['user_history_path']):
                    os.makedirs(DATA_PATH + bot_config['user_history_path'])

                # create file if not exist (user storage)
                utils.create_user_storage()

                # create file if not exist (tip unregistered user )
                utils.create_unregistered_tip_storage()

                for msg in self.reddit.inbox.unread(limit=None):

                    if (type(msg) is not Message) and (type(msg) is not Comment):
                        bot_logger.logger.info('Not a good message !')
                        msg.reply(lang.message_not_supported)
                        self.mark_msg_read(msg)
                    else:
                        bot_logger.logger.info("%s - %s sub : %s" % (str(msg), msg.author.name, msg.subject))
                        msg_body = msg.body.strip()
                        msg_subject = msg.subject.strip()
                        split_message = msg_body.split()

                        if msg_body == '+register' and msg_subject == '+register':
                            self.mark_msg_read(msg)
                            bot_command.register_user(self.rpc_main, msg)

                        elif msg_body == '+info' and msg_subject == '+info':
                            self.mark_msg_read(msg)
                            bot_command.info_user(self.rpc_main, msg)

                        elif msg_body == '+help' and msg_subject == '+help':
                            self.mark_msg_read(msg)
                            bot_command.help_user(self.rpc_main, msg)

                        elif msg_body == '+balance' and msg_subject == '+balance':
                            self.mark_msg_read(msg)
                            bot_command.balance_user(self.rpc_main, msg)

                        elif msg_body == '+history' and msg_subject == '+history':
                            self.mark_msg_read(msg)
                            bot_command.history_user(msg)

                        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
                            self.mark_msg_read(msg)
                            bot_command.withdraw_user(self.rpc_main, msg)

                        elif split_message.count('+/u/sodogetiptest'):
                            self.mark_msg_read(msg)
                            bot_command.tip_user(self.rpc_main, self.reddit, msg)

                        else:
                            self.mark_msg_read(msg)
                            # msg.reply('Currently not supported')
                            bot_logger.logger.info('Currently not supported')

                # to not explode rate limit :)
                bot_logger.logger.info('Make an pause !')
                time.sleep(3)
            except:
                traceback.print_exc()
                bot_logger.logger.error('Main Bot loop crashed...')
                time.sleep(10)

    def mark_msg_read(self, msg):
        unread_messages = [msg]
        self.reddit.inbox.mark_read(unread_messages)

    def process_pending_tip(self):
        while True:
            bot_logger.logger.info('Make clean of unregistered tips')
            bot_command.replay_remove_pending_tip(self.rpc_main, self.reddit)
            time.sleep(60)

    def anti_spamming_tx(self):
        # protect against spam attacks of an address having UTXOs.
        while True:
            bot_logger.logger.info('Make clean of tx')
            # get list of account
            list_account = user_function.get_users()
            for account, address in list_account.items():
                time.sleep(5)  # don't flood daemon
                list_tx = self.rpc_antispam.listunspent(1, 99999999999, [address])
                unspent_amounts = []
                for i in range(0, len(list_tx), 1):
                    unspent_amounts.append(list_tx[i]['amount'])
                    if i > 200:
                        break

                if len(list_tx) > int(bot_config['spam_limit']):
                    bot_logger.logger.info('Consolidate %s account !' % account)
                    amount = crypto.get_user_confirmed_balance(self.rpc_antispam, account)
                    crypto.send_to(self.rpc_antispam, address, address, sum(unspent_amounts), True)
            time.sleep(240)


if __name__ == "__main__":
    bot_logger.logger.info("Bot Started !!")
    while True:
        try:
            Bot = SoDogeTip()

            thread_master = Thread(target=Bot.main)
            thread_pending_tip = Thread(target=Bot.process_pending_tip)
            thread_anti_spamming_tx = Thread(target=Bot.anti_spamming_tx)

            thread_master.start()
            thread_pending_tip.start()
            thread_anti_spamming_tx.start()

            thread_master.join()
            thread_pending_tip.join()
            thread_anti_spamming_tx.join()

            bot_logger.logger.error('All bot task finished ...')
        except:
            traceback.print_exc()
            bot_logger.logger.error('Resuming in 30sec...')
            time.sleep(30)
