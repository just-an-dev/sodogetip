import datetime
import traceback

import bot_logger
import crypto
import lang
import user_function
import utils


def register_user(rpc, msg):
    if not user_function.user_exist(msg.author.name):
        address = rpc.getnewaddress("reddit-%s" % msg.author.name)
        if address:
            msg.reply(lang.message_register_success % (msg.author.name, address) + lang.message_footer)
            user_function.add_user(msg.author.name, address)

            user_function.add_to_history(msg.author.name, "", "", "", "register")
        else:
            bot_logger.logger.warning('Error during register !')
    else:
        bot_logger.logger.info('%s are already registered ' % msg.author.name)
        msg.reply(lang.message_already_registered + lang.message_account_details + lang.message_footer)


def balance_user(rpc, msg):
    if user_function.user_exist(msg.author.name):
        balance = crypto.get_user_balance(rpc, msg.author.name)
        bot_logger.logger.info('user %s balance = %s' % (msg.author.name, balance))
        value_usd = utils.get_coin_value(balance)
        msg.reply(lang.message_balance % (msg.author.name, str(balance), str(value_usd)) + lang.message_footer)
        user_function.add_to_history(msg.author.name, "", "", balance, "balance")
    else:
        bot_logger.logger.info('user %s not registered ' % msg.author.name)
        msg.reply(lang.message_need_register + lang.message_footer)


def info_user(rpc, msg):
    if user_function.user_exist(msg.author.name):
        user_function.get_user_info(rpc, msg)
    else:
        msg.reply(lang.message_need_register + lang.message_footer)


def help_user(rpc, msg):
    msg.reply(lang.message_help + lang.message_footer)


def withdraw_user(rpc, msg):
    split_message = msg.body.strip().split()

    if user_function.user_exist(msg.author.name):
        sender_address = user_function.get_user_address(msg.author.name)
        amount = split_message[1]
        user_balance = crypto.get_user_balance(rpc, msg.author.name)
        if utils.check_amount_valid(amount):
            if int(amount) >= user_balance:
                bot_logger.logger.info('user %s not have enough to withdraw this amount (%s), balance = %s' % (
                    msg.author.name, amount, user_balance))
                msg.reply(lang.message_balance_low_withdraw % msg.author.name + lang.message_footer)
            else:
                receiver_address = split_message[4]
                try:
                    if crypto.send_to(rpc, sender_address, receiver_address, amount, True):
                        user_function.add_to_history(msg.author.name, sender_address, receiver_address, amount,
                                                     "withdraw")
                        msg.reply(lang.message_withdraw % (str(amount) , receiver_address) + lang.message_footer)

                except:
                    traceback.print_exc()
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            msg.reply(lang.message_invalid_amount + lang.message_footer)
    else:
        msg.reply(lang.message_need_register + lang.message_footer)


def tip_user(rpc, msg):
    bot_logger.logger.info('An user mention detected ')
    split_message = msg.body.lower().strip().split()
    tip_index = split_message.index('+/u/sodogetiptest')

    if split_message[tip_index] == '+/u/sodogetiptest' and split_message[tip_index + 2] == 'doge':
        amount = split_message[tip_index + 1]

        if utils.check_amount_valid(amount):
            parent_comment = msg.parent()
            if user_function.user_exist(msg.author.name):

                # check we have enough
                user_balance = crypto.get_user_balance(rpc, msg.author.name)
                if int(amount) >= user_balance:
                    bot_logger.logger.info('user %s not have enough to tip this amount (%s), balance = %s' % (
                        msg.author.name, amount, user_balance))
                    msg.reply(lang.message_balance_low_tip % (msg.author.name , parent_comment.author.name))
                else:

                    # check user have address before tip
                    if user_function.user_exist(parent_comment.author.name):
                        if crypto.tip_user(rpc, msg.author.name, parent_comment.author.name, amount):
                            user_function.add_to_history(msg.author.name, msg.author.name, parent_comment.author.name,
                                                         amount,
                                                         "tip send")
                            user_function.add_to_history(parent_comment.author.name, msg.author.name,
                                                         parent_comment.author.name,
                                                         amount,
                                                         "tip receive")

                            bot_logger.logger.info(
                                '%s tip %s to %s' % (msg.author.name, str(amount), parent_comment.author.name))
                            # if user have 'verify' in this command he will have confirmation
                            if split_message.count('verify') or int(amount) >= 1000:
                                value_usd = utils.get_coin_value(amount)
                                msg.reply(lang.message_tip % (msg.author.name, parent_comment.author.name, str(amount), str(value_usd)))
                    else:
                        user_function.save_unregistered_tip(msg.author.name, parent_comment.author.name, amount)
                        user_function.add_to_history(msg.author.name, msg.author.name, parent_comment.author.name,
                                                     amount,
                                                     "tip", False)
                        bot_logger.logger.info('user %s not registered' % parent_comment.author.name)
                        msg.reply(
                            '+/u/%s need [register](%s) before can be tipped (tip saved during 3 day)' % (
                                parent_comment.author.name, lang.link_register) + lang.message_footer
                        )
            else:
                msg.reply(lang.message_need_register)
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            msg.reply(lang.message_invalid_amount)


def history_user(msg):
    if user_function.user_exist(msg.author.name):
        data = user_function.get_user_history(msg.author.name)
        history_table = "Date|Sender|Receiver|Amount|Action|Finish|\n"
        history_table += ":-:|:-:|:-:|:-:|:-:|:-:\n"
        for tip in data:
            history_table += "%s|%s|%s|%s|%s|%s|\n" % (
                datetime.datetime.strptime(tip['time'], '%Y-%m-%dT%H:%M:%S.%f'), tip['sender'], tip['receiver'],
                str(tip['amount']), tip['action'], str(tip['finish']))

        msg.reply(lang.message_history % msg.author.name + history_table + lang.message_footer)
    else:
        bot_logger.logger.info('user %s not registered ' % msg.author.name)
        msg.reply(lang.message_need_register + lang.message_footer)


def replay_remove_pending_tip(rpc):
    # check if it's not too old & replay tipping
    limit_date = datetime.datetime.now() - datetime.timedelta(days=3)

    # check if user have pending tips
    list_tips = user_function.get_unregistered_tip()

    if list_tips:
        for tip in list_tips:
            if (datetime.datetime.strptime(tip['time'], '%Y-%m-%dT%H:%M:%S.%f') > limit_date):
                if (user_function.user_exist(tip['receiver'])):
                    bot_logger.logger.info(
                        "replay tipping - %s send %s to %s  " % (tip['sender'], tip['amount'], tip['receiver']))
                    crypto.tip_user(rpc, tip['sender'], tip['receiver'], tip['amount'])
            else:
                bot_logger.logger.info(
                    "delete old tipping - %s send %s for %s  " % (tip['sender'], tip['amount'], tip['receiver']))
                user_function.remove_pending_tip(tip['id'])
    else:
        bot_logger.logger.info("no pendding tipping")
