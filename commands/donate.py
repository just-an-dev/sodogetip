from jinja2 import Template

import bot_logger
import config
import crypto
import lang
import models
import utils


def donate(msg, tx_queue, failover_time):
    user = models.User(msg.author.name)
    if user.is_registered():
        split_message = msg.body.lower().strip().split()

        donate_index = split_message.index('+donate')
        amount = split_message[donate_index + 1]
        if utils.check_amount_valid(amount) and split_message[donate_index + 2] == 'doge':

            crypto.tip_user(user.username.address, models.User(config.bot_name).address, amount, tx_queue,
                            failover_time)

            models.HistoryStorage.add_to_history(msg.author.name, msg.author.name, config.bot_name, amount, "donate")
        else:
            bot_logger.logger.info(lang.message_invalid_amount)
            user.send_private_message('invalid amount', lang.message_invalid_amount)
    else:
        bot_logger.logger.info('user %s not registered (command : donate) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))
