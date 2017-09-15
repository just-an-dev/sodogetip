from jinja2 import Template

import bot_logger
import lang
import models


def help_user(msg):
    user = models.User(msg.author.name)
    if user.is_registered():
        msg.reply(Template(lang.message_help + lang.message_footer).render(
            username=msg.author.name, address=user.address))
    else:
        bot_logger.logger.info('user %s not registered (command : help) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))
