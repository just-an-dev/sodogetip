from jinja2 import Template

import bot_logger
import config
import history
import lang
import models


def hall_of_fame(msg):
    user = models.User(msg.author.name)
    if user.is_registered():
        message = "Donation Tip to " + config.bot_name + " : "
        donator_list = {}
        hist = history.get_user_history(config.bot_name)
        message += "\n\nUser|Donation Ammount|\n"

        for tip in hist:
            if tip["sender"] in donator_list.keys():
                donator_list[tip["sender"]] = float(donator_list[tip["sender"]]) + tip['amount']
            else:
                donator_list[tip["sender"]] = tip['amount']

        for donor in sorted(donator_list.items(), key=lambda user: user[1], reverse=True):
            message += "%s|%s|\n" % (donor[0], str(donor[1]))

        user.send_private_message("Hall Of Fame", message)
    else:
        bot_logger.logger.info('user %s not registered (command : hall_of_fame) ' % user.username)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=user.username))
