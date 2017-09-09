from jinja2 import Template

import bot_logger
import config
import crypto
import lang
import models


def vanity(msg):
    user = models.User(msg.author.name)
    if user.is_registered():

        v = models.VanityGenRequest(user)
        v.parse_message(msg.body.lower().strip())
        if len(v.pattern) not in config.vanitygen_price.keys():
            user.send_private_message("Vanity Request : Error",
                                      "Your request can't be process, pattern too long or too short")
        else:
            if v.save_resquest():
                # send money to vanity account

                amount = config.vanitygen_price[len(v.pattern)] - 2  # reduce fee to move funds after generation
                crypto.send_to(None, user.address, config.vanitygen_address, amount)

                # send message
                user.send_private_message("Vanity Request : Received", "Your request will be process in few time")
            else:
                # send error message
                user.send_private_message("Vanity Request : Error",
                                          "Your request can't be process, check your pattern is a valid base58 string, and start with D")
    else:
        bot_logger.logger.info('user %s not registered (command : vanity) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))
