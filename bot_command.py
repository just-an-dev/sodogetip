import re

from jinja2 import Template
from praw.models import Comment

import bot_logger
import crypto
import lang
import models
import user_function


# Resend tips to previously unregistered users that are now registered
def replay_pending_tip(reddit, tx_queue, failover_time):
    # check if user have pending tips
    list_tips = user_function.get_unregistered_tip()

    if list_tips:
        for arr_tip in list_tips:
            tip = models.Tip().create_from_array(arr_tip)

            bot_logger.logger.info("replay tipping check for %s" % str(tip.id))

            # check if it's not too old & replay tipping
            if not tip.is_expired():
                if tip.receiver.is_registered():
                    bot_logger.logger.info(
                        "replay tipping %s - %s send %s to %s  " % (
                            str(tip.id), tip.sender.username, tip.amount, tip.receiver.username))

                    tip.tx_id = crypto.tip_user(tip.sender.address, tip.receiver.address, tip.amount, tx_queue,
                                                failover_time)
                    if tip.tx_id:
                        tip.finish = True

                        user_function.remove_pending_tip(tip.id)

                        if tip.message_fullname is not None:
                            msg_id = re.sub(r't\d+_(?P<id>\w+)', r'\g<id>', tip.message_fullname)
                            msg = Comment(reddit, msg_id)
                            msg.reply(Template(lang.message_tip).render(
                                sender=tip.sender.username, receiver=tip.receiver.username, amount=str(tip.amount),
                                value_usd=str(tip.get_value_usd()), txid=tip.tx_id))

                else:
                    tip.status = "waiting registration of receiver"
                    bot_logger.logger.info(
                        "replay check for %s - user %s not registered " % (str(tip.id), tip.receiver.username))

            else:
                tip.status = "receiver not registered in time"
                tip.finish = ""
                bot_logger.logger.info(
                    "delete old tipping - %s send %s to %s  " % (
                        tip.sender.username, tip.amount, tip.receiver.username))
                user_function.remove_pending_tip(tip.id)

            # update tip status
            models.HistoryStorage.update_tip(tip.sender.username, tip)
            models.HistoryStorage.update_tip(tip.receiver.username, tip)
    else:
        bot_logger.logger.info("no pending tipping")


def enablemultisig_1of2(rpc, reddit, msg, tx_queue, failover_time):
    if user_function.user_exist(msg.author.name):
        split_message = msg.body.lower().strip().split()
        enablemultisig_index = split_message.index('+enablemultisig')
        if split_message[enablemultisig_index + 1] == '1of2':
            userpubkey = split_message[enablemultisig_index + 2]
            address = user_function.get_user_address(msg.author.name)
            botpubkey = rpc.validateaddress(address)
            try:
                multisig = rpc.createmultisig(1, [str(botpubkey['pubkey']), str(split_message[enablemultisig_index + 2])])
            except:
                bot_logger.logger.info('user %s entered invalid pubkey (command : enablemultisig_1of2) ' % msg.author.name)
            rpc.importaddress(multisig["address"], "redditmulti-%s" % msg.author.name, False)
            msg.reply('1 of 2 multisig successfully created.  Your address is : ' + str(multisig["address"]) + '\n\n and your redeemScript is : ' + multisig["redeemScript"])
