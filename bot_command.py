import datetime
import re
import time

from jinja2 import Template
from praw.models import Comment

import bot_logger
import config
import crypto
import history
import lang
import models
import user_function
import utils


def register_user(rpc, msg):
    if not user_function.user_exist(msg.author.name):
        address = rpc.getnewaddress("reddit-%s" % msg.author.name)
        if address:
            msg.reply(
                Template(lang.message_register_success + lang.message_footer).render(username=msg.author.name,
                                                                                     address=address))
            user_function.add_user(msg.author.name, address)

            history.add_to_history(msg.author.name, "", "", "", "register")

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

        history.add_to_history(msg.author.name, "", "", balance, "balance")
    else:
        bot_logger.logger.info('user %s not registered (command : balance) ' % msg.author.name)
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
        bot_logger.logger.info('user %s not registered (command : info) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def help_user(rpc, msg):
    if user_function.user_exist(msg.author.name):
        address = user_function.get_user_address(msg.author.name)
        msg.reply(Template(lang.message_help + lang.message_footer).render(
            username=msg.author.name, address=address))
    else:
        bot_logger.logger.info('user %s not registered (command : help) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def withdraw_user(rpc, msg, failover_time):
    split_message = msg.body.strip().split()

    if user_function.user_exist(msg.author.name):
        sender_address = user_function.get_user_address(msg.author.name)
        amount = float(split_message[1])
        amount = round(amount - 0.5)

        user_balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        user_spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name)

        if utils.check_amount_valid(amount) and split_message[4] != sender_address:
            if amount >= float(user_balance) + float(user_spendable_balance):
                bot_logger.logger.info('user %s not have enough to withdraw this amount (%s), balance = %s' % (
                    msg.author.name, amount, user_balance))
                msg.reply(Template(lang.message_balance_low_withdraw).render(
                    username=msg.author.name, user_balance=str(user_balance), amount=str(amount)) + lang.message_footer)
            else:
                receiver_address = split_message[4]
                if time.time() > int(failover_time.value) + 86400:
                    send = crypto.send_to(rpc, sender_address, receiver_address, amount)
                else:
                    send = crypto.send_to_failover(rpc, sender_address, receiver_address, amount)

                if send:
                    history.add_to_history(msg.author.name, sender_address, receiver_address, amount,
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
    bot_logger.logger.debug("failover_time : %s " % (str(failover_time.value)))

    # create an Tip
    tip = models.Tip()

    # update sender
    tip.set_sender(msg.author.name)

    # parse message
    tip.parse_message(msg.body, rpc)

    # check amount of tip
    if not utils.check_amount_valid(tip.amount):
        # invalid amount
        bot_logger.logger.info(lang.message_invalid_amount)
        reddit.redditor(msg.author.name).message('invalid amount', lang.message_invalid_amount)
        return False

    # check receiver
    if user_function.user_exist(tip.sender.username) and (tip.sender.username != tip.receiver.username):
        # update receiver
        tip.set_receiver(msg.parent().author.name)
    elif user_function.user_exist(msg.author.name) and (msg.author.name == tip.receiver.username):
        reddit.redditor(msg.author.name).message('cannot tip self',
                                                 Template(lang.message_recipient_self).render(
                                                     username=msg.author.name))
        return False
    else:
        reddit.redditor(msg.author.name).message('tipped user not registered',
                                                 Template(lang.message_need_register).render(
                                                     username=msg.author.name))
        return False

    # check we have enough
    user_spendable_balance = crypto.balance_user(rpc, msg, failover_time)
    bot_logger.logger.debug('user_spendable_balance = %s' % user_spendable_balance)

    # in failover we need to use only user_balance
    if tip.amount >= float(user_spendable_balance):
        user_pending_balance = crypto.get_user_unconfirmed_balance(rpc, msg.author.name)
        # not enough for tip
        if tip.amount < float(user_pending_balance):
            reddit.redditor(msg.author.name).message('pending tip',
                                                     Template(lang.message_balance_pending_tip).render(
                                                         username=msg.author.name))
        else:
            bot_logger.logger.info('user %s not have enough to tip this amount (%s), balance = %s' % (
                msg.author.name, str(tip.amount), str(user_spendable_balance)))
            reddit.redditor(msg.author.name).message('low balance',
                                                     Template(lang.message_balance_low_tip).render(
                                                         username=msg.author.name))
    else:
        # ok we have enough for tip
        value_usd = utils.get_coin_value(tip.amount)

        # check user have address before tip
        if user_function.user_exist(tip.receiver.username):
            tip.txid = crypto.tip_user(rpc, msg.author.name, tip.receiver.username, tip.amount, tx_queue, failover_time)
            if tip.txid:
                bot_logger.logger.info(
                    '%s tip %s to %s' % (msg.author.name, str(tip.amount), tip.receiver.username))

                # if user have 'verify' in this command he will have confirmation
                if tip.verify:
                    msg.reply(Template(lang.message_tip).render(
                        sender=msg.author.name, receiver=tip.receiver.username,
                        amount=str(int(tip.amount)),
                        value_usd=str(value_usd), txid=tip.txid
                    ))
        else:
            bot_logger.logger.info('user %s not registered' % tip.receiver.username)

            user_function.save_unregistered_tip(msg.author.name, tip.receiver.username, tip.amount,
                                                msg.fullname)

            # send message to sender of tip
            reddit.redditor(msg.author.name).message('tipped user not registered',
                                                     Template(lang.message_recipient_register).render(
                                                         username=tip.receiver.username))
            # send message to receiver
            reddit.redditor(tip.receiver.username).message(
                Template(
                    lang.message_recipient_need_register_title).render(amount=str(tip.amount)),
                Template(
                    lang.message_recipient_need_register_message).render(
                    username=tip.receiver.username, sender=msg.author.name, amount=str(tip.amount),
                    value_usd=str(value_usd)))

        # add tip to history of sender & receiver
        history.add_to_history(msg.author.name, msg.author.name, tip.receiver.username,
                               tip.amount,
                               "tip send", tip.txid)
        history.add_to_history(tip.receiver.username, msg.author.name,
                               tip.receiver.username,
                               tip.amount,
                               "tip receive", tip.txid)


def history_user(msg):
    if user_function.user_exist(msg.author.name):
        data = history.get_user_history(msg.author.name)
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
        bot_logger.logger.info('user %s not registered (command : history) ' % msg.author.name)
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


def donate(rpc, reddit, msg, tx_queue, failover_time):
    if user_function.user_exist(msg.author.name):
        split_message = msg.body.lower().strip().split()

        donate_index = split_message.index('+donate')
        amount = split_message[donate_index + 1]
        if utils.check_amount_valid(amount) and split_message[donate_index + 2] == 'doge':
            tip_user(rpc, msg.author.name, config.bot_name, amount, tx_queue, failover_time)
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            reddit.redditor(msg.author.name).message('invalid amount', lang.message_invalid_amount)
    else:
        bot_logger.logger.info('user %s not registered (command : donate) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))
