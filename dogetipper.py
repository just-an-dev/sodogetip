import time
import traceback

import praw
import requests
from praw.models import Message, Comment
from tinydb import TinyDB

import bot_command
import bot_logger
import config
import crypto
import lang
import reddit_gold
import utils
from models import UserStorage


class SoDogeTip:
    def __init__(self):
        self.reddit = praw.Reddit(config.bot_name)

    def main(self, tx_queue, failover_time):
        bot_logger.logger.info('Main Bot loop !')

        while True:
            bot_logger.logger.debug('main failover_time : %s' % str(failover_time.value))

            try:

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
                            bot_command.register_user(msg, self.reddit)
                            utils.mark_msg_read(self.reddit, msg)

                        elif (msg_body == '+info' and msg_subject == '+info') or (
                                        msg_body == '+balance' and msg_subject == '+balance'):
                            bot_command.info_user(msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif msg_body == '+help' and msg_subject == '+help':
                            bot_command.help_user(msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif msg_body == '+history' and msg_subject == '+history':
                            bot_command.history_user(msg)
                            utils.mark_msg_read(self.reddit, msg)

                        elif split_message.count('+withdraw') and msg_subject == '+withdraw':
                            utils.mark_msg_read(self.reddit, msg)
                            bot_command.withdraw_user(msg, failover_time)

                        elif split_message.count('+/u/' + config.bot_name):
                            utils.mark_msg_read(self.reddit, msg)
                            bot_command.tip_user(self.reddit, msg, tx_queue, failover_time)

                        elif split_message.count('+donate'):
                            utils.mark_msg_read(self.reddit, msg)
                            bot_command.donate(self.reddit, msg, tx_queue, failover_time)

                        elif msg_subject == '+gold' or msg_subject == '+gild':
                            reddit_gold.gold(self.reddit, msg, tx_queue, failover_time)
                            utils.mark_msg_read(self.reddit, msg)

                        else:
                            utils.mark_msg_read(self.reddit, msg)
                            # msg.reply('Currently not supported')
                            bot_logger.logger.info('Currently not supported')

                # to not explode rate limit :)
                bot_logger.logger.info('Make an pause !')
                time.sleep(3)
            except:
                traceback.print_exc()
                bot_logger.logger.error('Main Bot loop crashed...')
                time.sleep(10)

    def process_pending_tip(self, tx_queue, failover_time):
        while True:
            bot_logger.logger.info('Make clean of unregistered tips')
            bot_command.replay_remove_pending_tip(self.reddit, tx_queue, failover_time)
            time.sleep(60)

    def anti_spamming_tx(self):
        # protect against spam attacks of an address having UTXOs.
        while True:
            rpc_antispam = crypto.get_rpc()

            bot_logger.logger.info('Make clean of tx')
            # get list of account
            list_account = UserStorage.get_users()
            for account in list_account.items():
                address = UserStorage.get_user_address(account)
                # don't flood rpc daemon
                time.sleep(1)
                list_tx = rpc_antispam.listunspent(1, 99999999999, [address])

                if len(list_tx) > int(config.spam_limit):
                    unspent_amounts = []
                    for i in range(0, len(list_tx), 1):
                        unspent_amounts.append(list_tx[i]['amount'])
                        # limits to 200 transaction to not explode timeout rpc
                        if i > 200:
                            break

                    bot_logger.logger.info('Consolidate %s account !' % account)
                    crypto.send_to(rpc_antispam, address, address, sum(unspent_amounts), True)

            # wait a bit before re-scan account
            time.sleep(240)

    def double_spend_check(self, tx_queue, failover_time):
        while True:
            bot_logger.logger.info('Check double spend')
            time.sleep(1)
            sent_tx = tx_queue.get()
            bot_logger.logger.info('Check double spend on tx %s' % sent_tx)
            try:
                tx_info = requests.get(config.url_get_value['blockcypher'] + sent_tx).json()
                if tx_info["double_spend"] is False:
                    # check we are not in safe mode
                    if time.time() > int(failover_time.value) + 86400:
                        bot_logger.logger.warn('Safe mode Disabled')
                        failover_time.value = 0

                elif tx_info["double_spend"] is True:
                    # update time until we are in safe mode
                    bot_logger.logger.warn('Double spend detected on tx %s' % sent_tx)
                    failover_time.value = int(time.time())
            except:
                traceback.print_exc()

            bot_logger.logger.debug('failover_time : %s' % str(failover_time.value))

    def vanitygen(self, tx_queue, failover_time):
        while True:
            bot_logger.logger.info('Check if we need to generate address')
            # get user request of gen
            db = TinyDB(DATA_PATH + bot_config['vanitygen'])
            for gen_request in db.all():
                print gen_request

                # generate address

                # parse output

                # transfer funds

                # update user storage file
