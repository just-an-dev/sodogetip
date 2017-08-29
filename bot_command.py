import random
import re

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


def register_user(msg):
    user = models.User(msg.author.name)
    if not user.is_registered():
        user.get_new_address()
        if user.address:
            content_reply = Template(lang.message_register_success + lang.message_footer).render(
                username=user.username,
                address=user.address)
            tittle_reply = 'you are registered'

            user.register()
            history.add_to_history(msg.author.name, "", "", "", "register")

            # create a backup of wallet
            crypto.backup_wallet()
        else:
            bot_logger.logger.warning('Error during register !')
    else:
        bot_logger.logger.info('%s are already registered ' % user.username)

        # pending_tips is balance of tip send to unregistered users
        pending_tips = user.get_balance_pending_tip()
        unconfirmed_balance = user.get_balance_unconfirmed()
        spendable_balance = user.get_balance(user.address)

        bot_logger.logger.info('user %s spendable_balance = %s' % (user.username, spendable_balance))

        unconfirmed_value_usd = utils.get_coin_value(unconfirmed_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        pending_tips_value_usd = utils.get_coin_value(pending_tips)

        content_reply = Template(
            lang.message_already_registered + lang.message_account_details + lang.message_footer).render(
            username=msg.author.name,
            address=user.address,
            spendable_balance=str(spendable_balance),
            spendable_value_usd=str(spendable_value_usd),
            unconfirmed_balance=str(unconfirmed_balance),
            unconfirmed_value_usd=str(unconfirmed_value_usd),
            pending_tips=str(pending_tips),
            pending_tips_value_usd=str(pending_tips_value_usd)
        )
        tittle_reply = 'you are already registered'

    # send PM so just reply
    if type(msg) is Message:
        msg.reply(content_reply)

    # we have just comment so send info in PM
    if type(msg) is Comment:
        user.send_private_message(tittle_reply, content_reply)


def info_user(msg):
    user = models.User(msg.author.name)
    if user.is_registered():

        # pending_tips is balance of tip send to unregistered users
        pending_tips = user.get_balance_pending_tip()
        unconfirmed_balance = user.get_balance_unconfirmed()
        spendable_balance = user.get_balance(user.address)

        bot_logger.logger.info('user %s spendable_balance = %s' % (user.username, spendable_balance))

        unconfirmed_value_usd = utils.get_coin_value(unconfirmed_balance)
        spendable_value_usd = utils.get_coin_value(spendable_balance)
        pending_tips_value_usd = utils.get_coin_value(pending_tips)

        msg.reply(Template(lang.message_account_details + lang.message_footer).render(
            username=user.username,
            spendable_balance=str(spendable_balance),
            spendable_value_usd=str(spendable_value_usd),
            unconfirmed_balance=str(unconfirmed_balance),
            unconfirmed_value_usd=str(unconfirmed_value_usd),
            pending_tips=str(pending_tips),
            pending_tips_value_usd=str(pending_tips_value_usd),
            address=user.address))

        history.add_to_history(user.username, "", "", spendable_balance, "info")
    else:
        bot_logger.logger.info('user %s not registered (command : info) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def help_user(msg):
    user = models.User(msg.author.name)
    if user.is_registered():
        msg.reply(Template(lang.message_help + lang.message_footer).render(
            username=msg.author.name, address=user.address))
    else:
        bot_logger.logger.info('user %s not registered (command : help) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def withdraw_user(msg, failover_time):
    split_message = msg.body.strip().split()

    user = models.User(msg.author.name)
    if user.is_registered():

        if utils.check_amount_valid(split_message[1]) and split_message[4] != user.address:
            amount = float(split_message[1])
            amount = round(amount - 0.5)

            user_balance = user.get_balance()

            if amount >= float(user_balance):
                bot_logger.logger.info('user %s not have enough to withdraw this amount (%s), balance = %s' % (
                    user.username, amount, user_balance))
                msg.reply(Template(lang.message_balance_low_withdraw).render(
                    username=user.username, user_balance=str(user_balance), amount=str(amount)) + lang.message_footer)
            else:
                receiver_address = split_message[4]
                tip_id = random.randint(0, 99999999)

                history.add_to_history(user.username, user.username, receiver_address, amount, "withdraw", "", tip_id)

                send = crypto.tip_user(user.address, receiver_address, amount, None, failover_time)

                if send:
                    history.update_withdraw(user.username, True, send, tip_id)

                    value_usd = utils.get_coin_value(amount)
                    msg.reply(Template(lang.message_withdraw + lang.message_footer).render(
                        username=user.username, receiver_address=receiver_address, amount=str(amount),
                        value_usd=str(value_usd)))

        elif split_message[4] == user.address:
            msg.reply(lang.message_withdraw_to_self + lang.message_footer)
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            msg.reply(lang.message_invalid_amount + lang.message_footer)
    else:
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def tip_user(msg, tx_queue, failover_time):
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
        tip.sender.send_private_message('invalid amount', lang.message_invalid_amount)
        return False

    if tip.currency is None:
        bot_logger.logger.info(lang.message_invalid_currency)
        tip.sender.send_private_message('invalid currency', lang.message_invalid_currency)
        return False

    # update receiver
    tip.set_receiver(msg.parent().author.name)

    # check user not tip self
    if tip.sender.username == tip.receiver.username:
        tip.sender.send_private_message('cannot tip self',
                                        Template(lang.message_recipient_self).render(
                                                         username=tip.sender.username))
        return False

    # check sender have enough
    user_spendable_balance = tip.sender.get_balance(failover_time)
    bot_logger.logger.debug('user_spendable_balance = %s' % user_spendable_balance)

    # check user not send more they have
    if tip.amount > float(user_spendable_balance):
        user_pending_balance = tip.sender.get_balance_unconfirmed()
        # not enough for tip
        if tip.amount < float(user_pending_balance):
            tip.sender.send_private_message('pending tip',
                                            Template(lang.message_balance_pending_tip).render(
                                                             username=tip.sender.username))
        else:
            bot_logger.logger.info('user %s not have enough to tip this amount (%s), balance = %s' % (
                tip.sender.username, str(tip.amount), str(user_spendable_balance)))
            tip.sender.send_private_message('low balance',
                                            Template(lang.message_balance_low_tip).render(
                                                             username=tip.sender.username))

    else:
        # add tip to history of sender & receiver
        history.add_to_history_tip(tip.sender.username, "tip send", tip)
        history.add_to_history_tip(tip.receiver.username, "tip receive", tip)

        # check user who receive tip have an account
        if tip.receiver.is_registered():
            tip.tx_id = crypto.tip_user(tip.sender.address, tip.receiver.address, tip.amount, tx_queue,
                                        failover_time)
            if tip.tx_id:
                tip.finish = True
                tip.status = 'ok'

                bot_logger.logger.info(
                    '%s tip %s to %s' % (msg.author.name, str(tip.amount), tip.receiver.username))

                # if user have 'verify' in this command he will have confirmation
                if tip.verify:
                    msg.reply(Template(lang.message_tip).render(
                        sender=tip.sender.username, receiver=tip.receiver.username,
                        amount=str(int(tip.amount)),
                        value_usd=str(tip.get_value_usd()), txid=tip.tx_id
                    ))
        else:
            bot_logger.logger.info('user %s not registered (receiver)' % tip.receiver.username)
            tip.status = "waiting registration of receiver"

            # save tip
            user_function.save_unregistered_tip(tip)

            # send message to sender of tip
            tip.sender.send_private_message('tipped user not registered',
                                            Template(lang.message_recipient_register).render(
                                                             username=tip.receiver.username))
            # send message to receiver
            tip.receiver.send_private_message(
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
def replay_pending_tip(reddit, tx_queue, failover_time):
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

                    tip.tx_id = crypto.tip_user(tip.sender.address, tip.receiver.address, tip.amount, tx_queue,
                                                failover_time)
                    if tip.tx_id:
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


def donate(msg, tx_queue, failover_time):
    user = models.User(msg.author.name)
    if user.is_registered():
        split_message = msg.body.lower().strip().split()

        donate_index = split_message.index('+donate')
        amount = split_message[donate_index + 1]
        if utils.check_amount_valid(amount) and split_message[donate_index + 2] == 'doge':

            crypto.tip_user(user.username.address, models.User(config.bot_name).address, amount, tx_queue,
                            failover_time)

            history.add_to_history(msg.author.name, msg.author.name, config.bot_name, amount, "donate")
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            user.send_private_message('invalid amount', lang.message_invalid_amount)
    else:
        bot_logger.logger.info('user %s not registered (command : donate) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))


def vanity(msg):
    user = models.User(msg.author.name)
    if user.is_registered():

        v = models.VanityGenRequest(user)
        v.parse_message(msg.body.lower().strip())
        if v.save_resquest():
            # todo : send money to vanity account
            amount = config.vanitygen[len(v.pattern)] - 1  # reduce fee to move funds after generation

            # todo: send message
            pass
        else:
            # todo: send error message
            pass

    else:
        bot_logger.logger.info('user %s not registered (command : donate) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))
