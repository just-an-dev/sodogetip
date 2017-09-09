from jinja2 import Template
from praw.models import Comment, Message

import bot_logger
import crypto
import lang
import models
import utils
from models import history


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
        spendable_balance = user.get_balance()

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
