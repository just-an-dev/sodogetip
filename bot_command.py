import time
import datetime
import traceback

from jinja2 import Template
from praw.models import Comment

import bot_logger
import config
import crypto
import lang
import re
import user_function
import utils
import dogetipper


def register_user(rpc, msg):
    if not user_function.user_exist(msg.author.name):
        address = rpc.getnewaddress("reddit-%s" % msg.author.name)
        if address:
            msg.reply(
                Template(lang.message_register_success + lang.message_footer).render(username=msg.author.name,
                                                                                     address=address))
            user_function.add_user(msg.author.name, address)

            user_function.add_to_history(msg.author.name, "", "", "", "register")

            # create a backup of wallet
            rpc.backupwallet(
                config.backup_wallet_path + "backup_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + ".dat")
        else:
            bot_logger.logger.warning('Error during register !')
    else:
        bot_logger.logger.info('%s are already registered ' % msg.author.name)
        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        address = user_function.get_user_address(msg.author.name)
        msg.reply(Template(lang.message_already_registered + lang.message_account_details + lang.message_footer).render(
            username=msg.author.name,
            address=address, balance=str(balance))
        )


def balance_user(rpc, msg):
    if user_function.user_exist(msg.author.name):

        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        pending_balance = crypto.get_user_unconfirmed_balance(rpc, msg.author.name)
        spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name) + balance
        bot_logger.logger.info('user %s balance = %s' % (msg.author.name, balance))

        balance_value_usd = utils.get_coin_value(balance)
        pending_value_usd = utils.get_coin_value(pending_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        msg.reply(
            Template(lang.message_balance + lang.message_footer).render(username=msg.author.name, balance=str(balance),
                                                                        balance_value_usd=str(balance_value_usd),
                                                                        pendingbalance=str(pending_balance),
                                                                        pending_value_usd=str(pending_value_usd),
                                                                        spendablebalance=str(spendable_balance),
                                                                        spendable_value_usd=str(spendable_value_usd)))

        user_function.add_to_history(msg.author.name, "", "", balance, "balance")
    else:
        bot_logger.logger.info('user %s not registered ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def info_user(rpc, msg):
    if user_function.user_exist(msg.author.name):
        address = user_function.get_user_address(msg.author.name)
        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        pending_balance = crypto.get_user_unconfirmed_balance(rpc, msg.author.name)
        spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name) + balance
        balance_value_usd = utils.get_coin_value(balance)
        pending_value_usd = utils.get_coin_value(pending_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        msg.reply(Template(lang.message_account_details + lang.message_footer).render(
            username=msg.author.name,
            balance=str(balance),
            balance_value_usd=str(balance_value_usd),
            pendingbalance=str(pending_balance),
            pending_value_usd=str(pending_value_usd),
            spendablebalance=str(spendable_balance),
            spendable_value_usd=str(spendable_value_usd),
            address=address))

    else:
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def help_user(rpc, msg):
    if user_function.user_exist(msg.author.name):
        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        address = user_function.get_user_address(msg.author.name)
        msg.reply(Template(lang.message_help + lang.message_account_details + lang.message_footer).render(
            username=msg.author.name, address=address,
            balance=str(
                balance)))
    else:
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def withdraw_user(rpc, msg, failover_time):
    split_message = msg.body.strip().split()

    if user_function.user_exist(msg.author.name):
        sender_address = user_function.get_user_address(msg.author.name)
        amount = split_message[1]
        user_balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        user_spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name)
        if utils.check_amount_valid(amount) and split_message[4] != sender_address:
            if int(amount) >= user_balance + user_spendable_balance:
                bot_logger.logger.info('user %s not have enough to withdraw this amount (%s), balance = %s' % (
                    msg.author.name, amount, user_balance))
                msg.reply(lang.message_balance_low_withdraw.render(
                    username=msg.author.name, user_balance=str(user_balance), amount=str(amount)) + lang.message_footer)
            else:
                receiver_address = split_message[4]
                if time.time() > failover_time + 86400:
                    send = crypto.send_to(rpc, sender_address, receiver_address, amount)
                else:
                    send = crypto.send_to_failover(rpc, sender_address, receiver_address, amount)

                if send:
                    user_function.add_to_history(msg.author.name, sender_address, receiver_address, amount,
                                                 "withdraw")
                    value_usd = utils.get_coin_value(amount)
                    msg.reply(Template(lang.message_withdraw + lang.message_footer).render(
                        username=msg.author.name, receiver_address=receiver_address, amount=str(amount),
                        value_usd=str(value_usd)))

        elif split_message[4] == sender_address:
            msg.reply(lang.message_withdraw_to_self + lang.message_footer)
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            msg.reply(lang.message_invalid_amount + lang.message_footer)
    else:
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def tip_user(rpc, reddit, msg, tx_queue, failover_time):
    bot_logger.logger.info('An user mention detected ')
    split_message = msg.body.lower().strip().split()
    tip_index = split_message.index(str('+/u/' + config.bot_name))

    if split_message[tip_index] == str('+/u/' + config.bot_name) and split_message[tip_index + 2] == 'doge':

        amount = split_message[tip_index + 1]

        if utils.check_amount_valid(amount):
            parent_comment = msg.parent()
            if user_function.user_exist(msg.author.name) and (msg.author.name != parent_comment.author.name):

                # check we have enough
                user_balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
                user_pending_balance = crypto.get_user_unconfirmed_balance(rpc, msg.author.name)
                user_spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name) + user_balance
                if int(amount) >= user_spendable_balance:
                    # not enough for tip
                    if int(amount) < (user_spendable_balance + user_pending_balance):
                        msg.reply(Template(lang.message_balance_pending_tip).render(username=msg.author.name))
                    else:
                        bot_logger.logger.info('user %s not have enough to tip this amount (%s), balance = %s' % (
                            msg.author.name, str(amount), str(user_balance)))
                        msg.reply(Template(lang.message_balance_low_tip).render(username=msg.author.name))
                else:

                    value_usd = utils.get_coin_value(amount)

                    # check user have address before tip
                    if user_function.user_exist(parent_comment.author.name):
                        txid = crypto.tip_user(rpc, msg.author.name, parent_comment.author.name, amount, tx_queue,
                                               failover_time)
                        if txid:
                            user_function.add_to_history(msg.author.name, msg.author.name, parent_comment.author.name,
                                                         amount,
                                                         "tip send", txid)
                            user_function.add_to_history(parent_comment.author.name, msg.author.name,
                                                         parent_comment.author.name,
                                                         amount,
                                                         "tip receive", txid)

                            bot_logger.logger.info(
                                '%s tip %s to %s' % (msg.author.name, str(amount), parent_comment.author.name))
                            # if user have 'verify' in this command he will have confirmation
                            if split_message.count('verify') or int(amount) >= 1000:
                                msg.reply(Template(lang.message_tip).render(
                                    sender=msg.author.name, receiver=parent_comment.author.name, amount=str(amount),
                                    value_usd=str(value_usd), txid=txid
                                ))
                    else:
                        user_function.save_unregistered_tip(msg.author.name, parent_comment.author.name, amount,
                                                            msg.fullname)
                        user_function.add_to_history(msg.author.name, msg.author.name, parent_comment.author.name,
                                                     amount,
                                                     "tip send", False)
                        user_function.add_to_history(parent_comment.author.name, msg.author.name,
                                                     parent_comment.author.name,
                                                     amount,
                                                     "tip receive", False)
                        bot_logger.logger.info('user %s not registered' % parent_comment.author.name)
                        msg.reply(Template(lang.message_recipient_register).render(username=parent_comment.author.name))

                        reddit.redditor(parent_comment.author.name).message(
                            Template(
                                lang.message_recipient_need_register_title).render(amount=str(amount)),
                            Template(
                                lang.message_recipient_need_register_message).render(
                                username=parent_comment.author.name, sender=msg.author.name, amount=str(amount),
                                value_usd=str(value_usd)))
            elif user_function.user_exist(msg.author.name) and (msg.author.name == parent_comment.author.name):
                msg.reply(Template(lang.message_recipient_self).render(username=msg.author.name))
            else:
                msg.reply(Template(lang.message_need_register).render(username=msg.author.name))
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            msg.reply(lang.message_invalid_amount)


def history_user(msg):
    if user_function.user_exist(msg.author.name):
        data = user_function.get_user_history(msg.author.name)
        history_table = "\n\nDate|Sender|Receiver|Amount|Action|Finish|\n"
        history_table += "---|---|---|---|:-:|:-:\n"
        for tip in data:
            str_finish = "Pending"

            if tip['finish']:
                str_finish = "Successful"

            history_table += "%s|%s|%s|%s|%s|%s|\n" % (
                datetime.datetime.strptime(tip['time'], '%Y-%m-%dT%H:%M:%S.%f'), tip['sender'], tip['receiver'],
                str(tip['amount']), tip['action'], str_finish)

        msg.reply(Template(lang.message_history + history_table + lang.message_footer).render(username=msg.author.name))
    else:
        bot_logger.logger.info('user %s not registered ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


# Resend tips to previously unregistered users that are now registered
def replay_remove_pending_tip(rpc, reddit, tx_queue, failover_time):
    # check if it's not too old & replay tipping
    limit_date = datetime.datetime.now() - datetime.timedelta(days=3)

    # check if user have pending tips
    list_tips = user_function.get_unregistered_tip()

    if list_tips:
        for tip in list_tips:
            bot_logger.logger.info("replay tipping check for %s" % str(tip['id']))
            if (datetime.datetime.strptime(tip['time'], '%Y-%m-%dT%H:%M:%S.%f') > limit_date):
                if (user_function.user_exist(tip['receiver'])):
                    bot_logger.logger.info(
                        "replay tipping %s - %s send %s to %s  " % (
                            str(tip['id']), tip['sender'], tip['amount'], tip['receiver']))
                    txid = crypto.tip_user(rpc, tip['sender'], tip['receiver'], tip['amount'], tx_queue, failover_time)
                    user_function.remove_pending_tip(tip['id'])

                    value_usd = utils.get_coin_value(tip['amount'])

                    if 'message_fullname' in tip.keys():
                        msg_id = re.sub(r't\d+_(?P<id>\w+)', r'\g<id>', tip['message_fullname'])
                        msg = Comment(reddit, msg_id)
                        msg.reply(Template(lang.message_tip).render(
                            sender=tip['sender'], receiver=tip['receiver'], amount=str(tip['amount']),
                            value_usd=str(value_usd), txid=txid))

                else:
                    bot_logger.logger.info(
                        "replay check for %s - user %s not registered " % (str(tip['id']), tip['receiver']))
            else:
                bot_logger.logger.info(
                    "delete old tipping - %s send %s for %s  " % (tip['sender'], tip['amount'], tip['receiver']))
                user_function.remove_pending_tip(tip['id'])
    else:
        bot_logger.logger.info("no pending tipping")
