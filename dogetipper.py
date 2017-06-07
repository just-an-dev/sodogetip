import os
import time
import traceback
from threading import Thread

import praw
import requests
from bitcoinrpc.authproxy import AuthServiceProxy
from praw.models import Message, Comment

import bot_command
import bot_logger
import config
import crypto
import lang
import user_function
import utils
from config import rpc_config, bot_config, DATA_PATH


class SoDogeTip():
    def __init__(self):
        self.reddit = praw.Reddit(config.bot_name)

        self.rpc_main = AuthServiceProxy("http://%s:%s@%s:%s" % (
            rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
            rpc_config['doge_rpc_port']), timeout=120)

        self.rpc_antispam = AuthServiceProxy("http://%s:%s@%s:%s" % (
            rpc_config['doge_rpc_username'], rpc_config['doge_rpc_password'], rpc_config['doge_rpc_host'],
            rpc_config['doge_rpc_port']), timeout=120)

    def main(self, tx_queue, failover_time):
        bot_logger.logger.info('Main Bot loop !')
        bot_logger.logger.debug("failover_time : %s " % (str(failover_time.value)))

        while True:
            bot_logger.logger.debug('main failover_time : %s' % str(failover_time.value))

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
                        utils.mark_msg_read(self.reddit, msg)
                    else:
                        bot_logger.logger.info("%s - %s sub : %s" % (str(msg), msg.author.name, msg.subject))
                        msg_body = msg.body.strip()
                        msg_subject = msg.subject.strip()
                        split_message = msg_body.lower().split()

                        if (msg_body == '+register' and msg_subject == '+register') or split_message.count('+register'):
                            bot_command.register_user(self.rpc_main, msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif msg_body == '+info' and msg_subject == '+info':
                            bot_command.info_user(self.rpc_main, msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif msg_body == '+help' and msg_subject == '+help':
                            bot_command.help_user(self.rpc_main, msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif msg_body == '+balance' and msg_subject == '+balance':
                            bot_command.balance_user(self.rpc_main, msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif msg_body == '+history' and msg_subject == '+history':
                            bot_command.history_user(msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
                            utils.mark_msg_read(self.reddit, msg)
                            bot_command.withdraw_user(self.rpc_main, msg, failover_time)

                        elif split_message.count('+/u/' + config.bot_name):
                            utils.mark_msg_read(self.reddit, msg)
                            bot_command.tip_user(self.rpc_main, self.reddit, msg, tx_queue, failover_time)

                        else:
                            utils.mark_msg_read(self.reddit, msg)
                            # msg.reply('Currently not supported')
                            bot_logger.logger.info('Currently not supported')
                            utils.mark_msg_read(self.reddit, msg)

                # to not explode rate limit :)
                bot_logger.logger.info('Make an pause !')
                time.sleep(3)
            except:
                traceback.print_exc()
                bot_logger.logger.error('Main Bot loop crashed...')
                time.sleep(10)

    def process_pending_tip(self,tx_queue, failover_time):
        while True:
            bot_logger.logger.info('Make clean of unregistered tips')
            bot_command.replay_remove_pending_tip(self.rpc_main, self.reddit, tx_queue, failover_time)
            time.sleep(60)

    def anti_spamming_tx(self):
        # protect against spam attacks of an address having UTXOs.
        while True:
            bot_logger.logger.info('Make clean of tx')
            # get list of account
            list_account = user_function.get_users()
            for account, address in list_account.items():
                time.sleep(1)  # don't flood daemon
                list_tx = self.rpc_antispam.listunspent(1, 99999999999, [address])
                unspent_amounts = []
                for i in range(0, len(list_tx), 1):
                    unspent_amounts.append(list_tx[i]['amount'])
                    if i > 200:
                        break

                if len(list_tx) > int(bot_config['spam_limit']):
                    bot_logger.logger.info('Consolidate %s account !' % account)
                    # amount = crypto.get_user_confirmed_balance(self.rpc_antispam, account)
                    crypto.send_to(self.rpc_antispam, address, address, sum(unspent_amounts), True)
            time.sleep(240)

    def double_spend_check(self, tx_queue, failover_time):
        while True:
            bot_logger.logger.debug('last failover_time : %s' % str(failover_time.value))

            bot_logger.logger.info('Check double spend')
            time.sleep(1)
            sent_tx = tx_queue.get()
            bot_logger.logger.info('Check double spend on tx %s' % sent_tx)
            try:
                #tx_info = requests.get(config.url_get_value['blockcypher'] + sent_tx).json()
                tx_info = {}
                tx_info["double_spend"] = True
                if tx_info["double_spend"] is False:
                    # check we are not in safe mode
                    if time.time() > int(failover_time.value) + 86400:
                        bot_logger.logger.warn('Safe mode Disabled')
                        failover_time.value = 0

                elif tx_info["double_spend"] is True:
                    bot_logger.logger.warn('Double spend detected on tx %s' % sent_tx)
                    failover_time.value = int(time.time())
            except:
                traceback.print_exc()
            bot_logger.logger.debug('failover_time : %s' % str(failover_time.value))
