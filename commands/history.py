import datetime

from jinja2 import Template

import bot_logger
import config
import lang
import models


def history_user(msg):
    user = models.User(msg.author.name)
    if user.is_registered():
        # get user history
        data_raw = user.get_history()
        # keep only 30 last entry
        data = data_raw[-30:]

        history_table = build_message(data)

        msg.reply(Template(lang.message_history + history_table + lang.message_footer).render(username=msg.author.name))
    else:
        bot_logger.logger.info('user %s not registered (command : history) ' % msg.author.name)
        msg.reply(Template(lang.message_need_register + lang.message_footer).render(username=msg.author.name))


def build_message(data):
    history_table = "\n\nDate|Sender|Receiver|Amount|Action|Finish|\n"
    history_table += "---|---|---|---|:-:|:-:\n"
    for tip in data[::-1]:
        str_finish = "Pending"

        if 'status' in tip.keys() and tip['status'] is not None and tip['status'] != "":
            str_finish = str_finish + ' - ' + tip['status']

        if tip['finish']:
            str_finish = "[Successful](" + config.block_explorer + tip['tx_id'] + ")"

        str_amount = ""
        if tip['amount'] != "":
            str_amount = str(float(tip['amount']))
            if float(tip['amount']).is_integer():
                str_amount = str(int(tip['amount']))

        history_table += "%s|%s|%s|%s|%s|%s|\n" % (
            datetime.datetime.strptime(tip['time'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S'),
            tip['sender'], tip['receiver'],
            str_amount, tip['action'], str_finish)

    return history_table
