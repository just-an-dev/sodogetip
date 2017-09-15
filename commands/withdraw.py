import random

from jinja2 import Template

import bot_logger
import crypto
import lang
import models
import utils


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

                models.HistoryStorage.add_to_history(user.username, user.username, receiver_address, amount, "withdraw",
                                                     "",
                                                     tip_id)

                send = crypto.tip_user(user.address, receiver_address, amount, None, failover_time)

                if send:
                    models.HistoryStorage.update_withdraw(user.username, True, send, tip_id)

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
        bot_logger.logger.info('user %s not registered (command : withdraw) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))