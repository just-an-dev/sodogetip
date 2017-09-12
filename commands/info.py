from jinja2 import Template

import bot_logger
import lang
import models
import utils


def info_user(msg):
    user = models.User(msg.author.name)
    if user.is_registered():

        # pending_tips is balance of tip send to unregistered users
        pending_tips = user.get_balance_pending_tip()
        unconfirmed_balance = user.get_balance_unconfirmed()
        spendable_balance = user.get_balance()

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

        models.HistoryStorage.add_to_history(user.username, "", "", spendable_balance, "info")
    else:
        bot_logger.logger.info('user %s not registered (command : info) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))
