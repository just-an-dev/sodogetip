import datetime
import traceback

from jinja2 import Template
from praw.models import Comment

import bot_logger
import config
import crypto
import lang
import re

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

            user_function.add_to_history(msg.author.name, "register")
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

        user_function.add_to_history(msg.author.name, "balance", balance)
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


def withdraw_user(rpc, msg):
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
                try:
                    if crypto.send_to(rpc, sender_address, receiver_address, amount):
                        user_function.add_to_history(msg.author.name, sender_address, receiver_address, amount,
                                                     "withdraw")
                        value_usd = utils.get_coin_value(amount)
                        msg.reply(Template(lang.message_withdraw + lang.message_footer).render(
                            username=msg.author.name, receiver_address=receiver_address, amount=str(amount),
                            value_usd=str(value_usd)))

                except:
                    traceback.print_exc()
        elif split_message[4] == sender_address:
            msg.reply(lang.message_withdraw_to_self + lang.message_footer)
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            msg.reply(lang.message_invalid_amount + lang.message_footer)
    else:
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def tip_user(rpc, reddit, msg):
    bot_logger.logger.info('An user mention detected ')

    # create an Tip
    tip = models.Tip()
    tip.parse_message(msg.body)
    # update sender
    tip.sender = msg.parent().author.name

    # check if ammount is valid
    if utils.check_amount_valid(tip.amount):
        # in case of valid amount update verify if
        if int(tip.amount) >= 1000:
            tip.verify = True
            # elif utils.is_keyword(tip.amount):
            # do something with keyword
    else:
        # return an error message
        bot_logger.logger.info(lang.message_invalid_amount)
        msg.reply(lang.message_invalid_amount)
        return False

    if user_function.user_exist(tip.receiver) and (tip.receiver != tip.sender):
        # check we have enough
        user_balance = crypto.get_user_confirmed_balance(rpc, tip.receiver)
        user_pending_balance = crypto.get_user_unconfirmed_balance(rpc, tip.receiver)
        user_spendable_balance = crypto.get_user_spendable_balance(rpc, tip.receiver) + user_balance
        if int(tip.amount) >= user_spendable_balance:
            # not enough for tip
            if int(tip.amount) < (user_spendable_balance + user_pending_balance):
                msg.reply(Template(lang.message_balance_pending_tip).render(username=tip.receiver))
            else:
                bot_logger.logger.info('user %s not have enough to tip this amount (%s), balance = %s' % (
                    tip.receiver, str(tip.amount), str(user_balance)))
                msg.reply(Template(lang.message_balance_low_tip).render(username=tip.receiver))

        else:
            value_usd = utils.get_coin_value(tip.amount)

            # check user have address before tip
            if user_function.user_exist(tip.sender):
                txid = crypto.tip_user(rpc, tip.receiver, tip.sender, tip.amount)
                if txid:
                    tip.tx_id = txid
                    tip.finish = True

                    user_function.add_to_history(tip.receiver, "tip send", tip)
                    user_function.add_to_history(tip.sender, "tip receive", tip)

                    bot_logger.logger.info('%s tip %s to %s' % (tip.receiver, str(tip.amount), tip.sender))

                    # if user have 'verify' in this command he will have confirmation
                    if tip.verify:
                        msg.reply(Template(lang.message_tip).render(
                            sender=tip.receiver, receiver=tip.sender, amount=str(tip.amount),
                            value_usd=str(value_usd), txid=txid
                        ))
            else:
                user_function.save_unregistered_tip(tip.receiver, tip.sender, tip.amount, msg.fullname)
                user_function.add_to_history(tip.receiver, "tip send", tip)
                user_function.add_to_history(tip.sender, "tip receive", tip)

                bot_logger.logger.info('user %s not registered' % tip.sender)
                msg.reply(Template(lang.message_recipient_register).render(username=tip.sender))

                reddit.redditor(tip.sender).message(
                    Template(
                        lang.message_recipient_need_register_title).render(amount=str(tip.amount)),
                    Template(
                        lang.message_recipient_need_register_message).render(
                        username=tip.sender, sender=tip.receiver, amount=str(tip.amount),
                        value_usd=str(value_usd)))
    elif user_function.user_exist(tip.receiver) and (tip.receiver == tip.sender):
        msg.reply(Template(lang.message_tipping_yourself).render(username=tip.receiver))
    else:
        msg.reply(Template(lang.message_need_register).render(username=tip.receiver))


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
def replay_remove_pending_tip(rpc, reddit):
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
                    txid = crypto.tip_user(rpc, tip['sender'], tip['receiver'], tip['amount'])
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
