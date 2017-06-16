import datetime
import re
import time

from jinja2 import Template
from praw.models import Comment, Message

import bot_logger
import config
import crypto
import history
import lang
import models
import user_function
import utils


def register_user(rpc, msg, reddit):
    user = models.User(msg.author.name)
    if not user.is_registered():
        user.address = rpc.getnewaddress("reddit-%s" % msg.author.name)
        if user.address:
            content_reply = Template(lang.message_register_success + lang.message_footer).render(
                username=user.username,
                address=user.address)
            tittle_reply = 'you are registered'

            user_function.add_user(msg.author.name, user.address)

            history.add_to_history(msg.author.name, "", "", "", "register")

            # create a backup of wallet
            rpc.backupwallet(
                config.backup_wallet_path + "backup_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + ".dat")
        else:
            bot_logger.logger.warning('Error during register !')
    else:
        bot_logger.logger.info('%s are already registered ' % msg.author.name)

        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        pending_balance = crypto.get_user_unconfirmed_balance(rpc, user)
        spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name) + balance
        pending_value_usd = utils.get_coin_value(pending_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        content_reply = Template(
            lang.message_already_registered + lang.message_account_details + lang.message_footer).render(
            username=msg.author.name,
            address=user.address,
            pending_balance=str(pending_balance),
            pending_value_usd=str(pending_value_usd),
            spendable_balance=str(spendable_balance),
            spendable_value_usd=str(spendable_value_usd)
        )
        tittle_reply = 'you are already registered'

    # send PM so just reply
    if type(msg) is Message:
        msg.reply(content_reply)
    # we have just comment so send info in PM
    if type(msg) is Comment:
        reddit.redditor(msg.author.name).message(tittle_reply, content_reply)


def balance_user(rpc, msg):
    user = models.User(msg.author.name)
    if user.is_registered():

        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        # pending_tips is balance of tip send to unregistered users
        pending_tips = user.get_balance_unregistered_tip()
        pending_balance = crypto.get_user_unconfirmed_balance(rpc, user)
        spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name) + balance

        bot_logger.logger.info('user %s balance = %s' % (msg.author.name, balance))

        balance_value_usd = utils.get_coin_value(balance)
        pending_value_usd = utils.get_coin_value(pending_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        pending_tips_value_usd = utils.get_coin_value(pending_tips)
        msg.reply(
            Template(lang.message_balance + lang.message_footer).render(username=msg.author.name, balance=str(balance),
                                                                        balance_value_usd=str(balance_value_usd),
                                                                        pending_balance=str(pending_balance),
                                                                        pending_value_usd=str(pending_value_usd),
                                                                        spendable_balance=str(spendable_balance),
                                                                        spendable_value_usd=str(spendable_value_usd),
                                                                        pending_tips=str(pending_tips),
                                                                        pending_tips_value_usd=str(
                                                                            pending_tips_value_usd)
                                                                        ))

        history.add_to_history(msg.author.name, "", "", balance, "balance")
    else:
        bot_logger.logger.info('user %s not registered (command : balance) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def info_user(rpc, msg):
    user = models.User(msg.author.name)
    if user.is_registered():
        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
        pending_balance = crypto.get_user_unconfirmed_balance(rpc, user)
        spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name) + balance
        pending_value_usd = utils.get_coin_value(pending_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        msg.reply(Template(lang.message_account_details + lang.message_footer).render(
            username=msg.author.name,
            pendingbalance=str(pending_balance),
            pending_value_usd=str(pending_value_usd),
            spendable_balance=str(spendable_balance),
            spendable_value_usd=str(spendable_value_usd),
            address=user.address))
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

        if utils.check_amount_valid(split_message[1]) and split_message[4] != sender_address:
            amount = float(split_message[1])
            amount = round(amount - 0.5)

            user_balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)
            user_spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name)

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

    # check user who use command is registered
    if user_function.user_exist(msg.author.name) is not True:
        bot_logger.logger.info('user %s not registered (sender) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))
        return False

    # create an Tip
    tip = models.Tip()

    # update sender
    tip.set_sender(msg.author.name)

    # parse message
    tip.parse_message(msg.body, rpc)

    # set reddit message id
    tip.message_fullname = msg.fullname

    # check amount of tip
    if not utils.check_amount_valid(tip.amount):
        # invalid amount
        bot_logger.logger.info(lang.message_invalid_amount)
        reddit.redditor(msg.author.name).message('invalid amount', lang.message_invalid_amount)
        return False

    # update receiver
    tip.set_receiver(msg.parent().author.name)

    # check user not tip self
    if tip.sender.username == tip.receiver.username:
        reddit.redditor(tip.sender.username).message('cannot tip self',
                                                     Template(lang.message_recipient_self).render(
                                                         username=tip.sender.username))
        return False

    # check we have enough
    user_spendable_balance = crypto.balance_user(rpc, msg, failover_time)
    bot_logger.logger.debug('user_spendable_balance = %s' % user_spendable_balance)

    # in failover we need to use only user_balance
    if tip.amount >= float(user_spendable_balance):
        user_pending_balance = crypto.get_user_unconfirmed_balance(rpc, tip.sender)
        # not enough for tip
        if tip.amount < float(user_pending_balance):
            reddit.redditor(tip.sender.username).message('pending tip',
                                                         Template(lang.message_balance_pending_tip).render(
                                                             username=tip.sender.username))
        else:
            bot_logger.logger.info('user %s not have enough to tip this amount (%s), balance = %s' % (
                tip.sender.username, str(tip.amount), str(user_spendable_balance)))
            reddit.redditor(tip.sender.username).message('low balance',
                                                         Template(lang.message_balance_low_tip).render(
                                                             username=tip.sender.username))

    else:
        # add tip to history of sender & receiver
        history.add_to_history_tip(tip.sender.username, "tip send", tip)
        history.add_to_history_tip(tip.receiver.username, "tip receive", tip)

        # check user who receive tip have an account
        if tip.receiver.is_registered():
            tip.tx_id = crypto.tip_user(rpc, msg.author.name, tip.receiver.username, tip.amount, tx_queue,
                                        failover_time)
            if tip.tx_id:
                bot_logger.logger.info(
                    '%s tip %s to %s' % (msg.author.name, str(tip.amount), tip.receiver.username))

                # if user have 'verify' in this command he will have confirmation
                if tip.verify:
                    msg.reply(Template(lang.message_tip).render(
                        sender=msg.author.name, receiver=tip.receiver.username,
                        amount=str(int(tip.amount)),
                        value_usd=str(tip.get_value_usd()), txid=tip.tx_id
                    ))
        else:
            bot_logger.logger.info('user %s not registered (receiver)' % tip.receiver.username)
            # save tip
            user_function.save_unregistered_tip(tip)

            # send message to sender of tip
            reddit.redditor(tip.sender.username).message('tipped user not registered',
                                                         Template(lang.message_recipient_register).render(
                                                             username=tip.receiver.username))
            # send message to receiver
            reddit.redditor(tip.receiver.username).message(
                Template(
                    lang.message_recipient_need_register_title).render(amount=str(tip.amount)),
                Template(
                    lang.message_recipient_need_register_message).render(
                    username=tip.receiver.username, sender=msg.author.name, amount=str(tip.amount),
                    value_usd=str(tip.get_value_usd())))

        # update tip status
        history.update_tip(tip.sender.username, tip)
        history.update_tip(tip.receiver.username, tip)


def history_user(msg):
    if user_function.user_exist(msg.author.name):
        data_raw = history.get_user_history(msg.author.name)
        data = data_raw[-30:]

        history_table = history.build_message(data)

        msg.reply(Template(lang.message_history + history_table + lang.message_footer).render(username=msg.author.name))
    else:
        bot_logger.logger.info('user %s not registered (command : history) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


# Resend tips to previously unregistered users that are now registered
def replay_remove_pending_tip(rpc, reddit, tx_queue, failover_time):
    # check if user have pending tips
    list_tips = user_function.get_unregistered_tip()

    if list_tips:
        for arr_tip in list_tips:
            tip = models.Tip().create_from_array(arr_tip)

            bot_logger.logger.info("replay tipping check for %s" % str(tip.id))

            # check if it's not too old & replay tipping
            if not tip.is_expired():
                if tip.receiver.is_registered():
                    bot_logger.logger.info(
                        "replay tipping %s - %s send %s to %s  " % (
                            str(tip.id), tip.sender.username, tip.amount, tip.receiver.username))

                    tip.tx_id = crypto.tip_user(rpc, tip.sender.username, tip.receiver.username, tip.amount, tx_queue,
                                                failover_time)
                    tip.finish = True
                    user_function.remove_pending_tip(tip.id)

                    if tip.message_fullname is not None:
                        msg_id = re.sub(r't\d+_(?P<id>\w+)', r'\g<id>', tip.message_fullname)
                        msg = Comment(reddit, msg_id)
                        msg.reply(Template(lang.message_tip).render(
                            sender=tip.sender.username, receiver=tip.receiver.username, amount=str(tip.amount),
                            value_usd=str(tip.get_value_usd()), txid=tip.tx_id))

                    # update tip status
                    history.update_tip(tip.sender.username, tip)
                    history.update_tip(tip.receiver.username, tip)

                else:
                    bot_logger.logger.info(
                        "replay check for %s - user %s not registered " % (str(tip.id), tip.receiver.username))
            else:
                bot_logger.logger.info(
                    "delete old tipping - %s send %s for %s  " % (
                    tip.sender.username, tip.amount, tip.receiver.username))
                user_function.remove_pending_tip(tip.id)
    else:
        bot_logger.logger.info("no pending tipping")


def donate(rpc, reddit, msg, tx_queue, failover_time):
    user = models.User(msg.author.name)
    if user.is_registered():
        split_message = msg.body.lower().strip().split()

        donate_index = split_message.index('+donate')
        amount = split_message[donate_index + 1]
        if utils.check_amount_valid(amount) and split_message[donate_index + 2] == 'doge':

            crypto.tip_user(rpc, user.username, config.bot_name, amount, tx_queue, failover_time)

            history.add_to_history(msg.author.name, msg.author.name, config.bot_name, amount, "donate")
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            reddit.redditor(msg.author.name).message('invalid amount', lang.message_invalid_amount)
    else:
        bot_logger.logger.info('user %s not registered (command : donate) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))
