from jinja2 import Template

import bot_logger
import config
import lang
import models
import utils


# register 2000 doge lolidragon http://downloadlink.com/whatever.txt
# delete lolidragon

def offer(reddit, msg, tx_queue, failover_time):
    if config.shop_enabled is True:
        split_message = msg.body.strip().split()

        user = models.User(msg.author.name)
        if user.is_registered():
            if split_message[0] == "register" and utils.check_amount_valid(split_message[1]):
                # register an offer
                models.Offer.create(split_message[3], split_message[1], split_message[2], split_message[4])

            if split_message[0] == "delete" and len(split_message) >= 2:
                # delete an offer & check keyword exist
                if models.Offer.exist(split_message[2]):
                    models.Offer.remove(split_message[2])

        else:
            bot_logger.logger.info('user %s not registered (command : vanity) ' % user.username)
            msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))
