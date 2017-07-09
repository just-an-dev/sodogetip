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


def info_user(rpc, msg):
    user = models.User(msg.author.name)
    if user.is_registered():
        balance = crypto.get_user_confirmed_balance(rpc, msg.author.name)

        # pending_tips is balance of tip send to unregistered users
        pending_tips = user.get_balance_unregistered_tip()

        pending_balance = crypto.get_user_unconfirmed_balance(rpc, user)
        spendable_balance = crypto.get_user_spendable_balance(rpc, msg.author.name) + balance

        bot_logger.logger.info('user %s balance = %s' % (msg.author.name, balance))
        bot_logger.logger.info('user %s spendable_balance = %s' % (msg.author.name, spendable_balance))

        pending_value_usd = utils.get_coin_value(pending_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        pending_tips_value_usd = utils.get_coin_value(pending_tips)

        msg.reply(Template(lang.message_account_details + lang.message_footer).render(
            username=msg.author.name,
            spendable_balance=str(spendable_balance),
            spendable_value_usd=str(spendable_value_usd),
            pending_balance=str(pending_balance),
            pending_value_usd=str(pending_value_usd),
            pending_tips=str(pending_tips),
            pending_tips_value_usd=str(pending_tips_value_usd),
            address=user.address))

        history.add_to_history(msg.author.name, "", "", spendable_balance, "info")
    else:
        bot_logger.logger.info('user %s not registered (command : info) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def help_user(rpc, msg):
    user = models.User(msg.author.name)
    if user.is_registered():
        msg.reply(Template(lang.message_help + lang.message_footer).render(
            username=msg.author.name, address=user.address))
    else:
        bot_logger.logger.info('user %s not registered (command : help) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def withdraw_user(rpc, msg, failover_time):
    split_message = msg.body.strip().split()

    user = models.User(msg.author.name)
    if user.is_registered():

        if utils.check_amount_valid(split_message[1]) and split_message[4] != user.address:
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

                history.add_to_history(msg.author.name, user.username, receiver_address, amount, "withdraw")

                if time.time() > int(failover_time.value) + 86400:
                    send = crypto.send_to(rpc, user.address, receiver_address, amount)
                else:
                    send = crypto.send_to_failover(rpc, user.address, receiver_address, amount)

                if send:
                    history.add_to_history(msg.author.name, user.username, receiver_address, amount,
                                           "withdraw", True, send)
                    value_usd = utils.get_coin_value(amount)
                    msg.reply(Template(lang.message_withdraw + lang.message_footer).render(
                        username=msg.author.name, receiver_address=receiver_address, amount=str(amount),
                        value_usd=str(value_usd)))

        elif split_message[4] == user.address:
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

    # check user who use command is registered
    if tip.sender.is_registered() is not True:
        bot_logger.logger.info('user %s not registered (sender) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))
        return False

    # parse message
    tip.parse_message(msg.body)

    # set reddit message id
    tip.message_fullname = msg.fullname

    # check amount of tip
    if not utils.check_amount_valid(tip.amount):
        # invalid amount
        bot_logger.logger.info(lang.message_invalid_amount)
        reddit.redditor(msg.author.name).message('invalid amount', lang.message_invalid_amount)
        return False

    if tip.currency is None:
        bot_logger.logger.info(lang.message_invalid_currency)
        reddit.redditor(msg.author.name).message('invalid currency', lang.message_invalid_currency)
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
            tip.tx_id = crypto.tip_user(rpc, tip.sender.address, tip.receiver.address, tip.amount, tx_queue,
                                        failover_time)
            if tip.tx_id:
                tip.finish = True
                tip.status = 'ok'

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
            tip.status = "waiting registration of receiver"

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
    user = models.User(msg.author.name)
    if user.is_registered():
        # get user history
        data_raw = history.get_user_history(user.username)
        # keep only 30 last entry
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

                    tip.tx_id = crypto.tip_user(rpc, tip.sender.address, tip.receiver.address, tip.amount, tx_queue,
                                                failover_time)
                    tip.finish = True
                    user_function.remove_pending_tip(tip.id)

                    if tip.message_fullname is not None:
                        msg_id = re.sub(r't\d+_(?P<id>\w+)', r'\g<id>', tip.message_fullname)
                        msg = Comment(reddit, msg_id)
                        msg.reply(Template(lang.message_tip).render(
                            sender=tip.sender.username, receiver=tip.receiver.username, amount=str(tip.amount),
                            value_usd=str(tip.get_value_usd()), txid=tip.tx_id))

                else:
                    tip.status = "waiting registration of receiver"
                    bot_logger.logger.info(
                        "replay check for %s - user %s not registered " % (str(tip.id), tip.receiver.username))

            else:
                tip.status = "receiver not registered in time"
                tip.finish = ""
                bot_logger.logger.info(
                    "delete old tipping - %s send %s to %s  " % (
                        tip.sender.username, tip.amount, tip.receiver.username))
                user_function.remove_pending_tip(tip.id)

            # update tip status
            history.update_tip(tip.sender.username, tip)
            history.update_tip(tip.receiver.username, tip)
    else:
        bot_logger.logger.info("no pending tipping")


def donate(rpc, reddit, msg, tx_queue, failover_time):
    user = models.User(msg.author.name)
    if user.is_registered():
        split_message = msg.body.lower().strip().split()

        donate_index = split_message.index('+donate')
        amount = split_message[donate_index + 1]
        if utils.check_amount_valid(amount) and split_message[donate_index + 2] == 'doge':

            crypto.tip_user(rpc, user.username.address, models.User(config.bot_name).address, amount, tx_queue,
                            failover_time)

            history.add_to_history(msg.author.name, msg.author.name, config.bot_name, amount, "donate")
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            reddit.redditor(user.username).message('invalid amount', lang.message_invalid_amount)
    else:
        bot_logger.logger.info('user %s not registered (command : donate) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))


# buy an reddit gold account for one month
def gold(rpc_main, msg, tx_queue, failover_time):
    gold_address = "DGo1dHhU2pRAyU58LgACYU3i3fpaZakG5u"
    value_gold = "2000"

    user = models.User(msg.author.name)
    if user.is_registered():
        if msg.body.strip() == 'buy':

            # todo : check if we have enough credits
            gold_month = 1
            if not gold_month >= 1:
                # todo : store in db want an gold, when bot have new credits a PM can be send
                msg.reply(Template(lang.message_gold_no_more).render(username=user.username))
                return False

            # check user confirmed balance is ok
            if user.get_balance_confirmed() >= value_gold:
                msg.reply(Template(lang.message_gold_no_enough_doge).render(username=user.username))
                return False

            # send amount of one month of gold to address
            tx_id = crypto.tip_user(rpc_main, user.address, gold_address, value_gold, tx_queue, failover_time)

            if tx_id:
                # todo : send gold reddit

                # todo : update user history

                # todo : update gold reddit table

                # todo : send succes message
                msg.reply(Template(lang.message_buy_gold_success).render(username=user.username))
            else:
                # todo : send error message
                msg.reply(Template(lang.message_buy_gold_error).render(username=user.username))

        else:
            # send info on reddit gold
            msg.reply(Template(lang.message_buy_gold).render(username=user.username))
    else:
        bot_logger.logger.info('user %s not registered (command : donate) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))
