import traceback

import datetime

import crypto
import user_function
import utils

linkRegister = '[register](http://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Bregister&message=%2Bregister)'


def register_user(rpc, msg):
    if not user_function.user_exist(msg.author.name):
        address = rpc.getnewaddress()
        if address:
            msg.reply(msg.author.name + ' registered, your address is ' + address)
            user_function.add_user(msg.author.name, address)

            pending_tips(rpc, msg)
        else:
            print 'Error during register !'
    else:
        print msg.author.name + ' are already registered '
        msg.reply('You are already registered ')


def pending_tips(rpc, msg):
    # check if user have pending tips
    pending_tips = user_function.get_user_pending_tip(msg.author.name)
    if pending_tips != False:
        for tip in pending_tips:
            # check if it's not too old & replay tipping
            limit_date = datetime.datetime.now() - datetime.timedelta(days=3)
            if (datetime.datetime.strptime(tip['time'],'%Y-%m-%dT%H:%M:%SZ') < limit_date):
                print "replay tipping - %s send %s for %s  " % (tip['sender'], tip['amount'], msg.author.name)
                crypto.tip_user(rpc, tip['sender'], msg.author.name, tip['amount'])

        user_function.remove_pending_tip(msg.author.name)


def balance_user(rpc, msg):
    if user_function.user_exist(msg.author.name):
        balance = crypto.get_user_balance(rpc, msg.author.name)
        print('user %s balance = %s' % (msg.author.name, balance))
        value_usd = utils.get_coin_value(balance)
        msg.reply('Your balance : ' + str(balance) + ' ( ' + str(value_usd) + '$ ) ')
    else:
        print('user %s not registered ' % (msg.author.name))
        msg.reply('You need %s before' % linkRegister)


def info_user(rpc, msg):
    if user_function.user_exist(msg.author.name):
        user_function.get_user_info(msg)
    else:
        msg.reply('You need %s before' % linkRegister)


def withdraw_user(rpc, msg):
    split_message = msg.body.strip().split()

    if user_function.user_exist(msg.author.name):
        sender_address = user_function.get_user_address(msg.author.name)
        amount = split_message[1]
        user_balance = crypto.get_user_balance(rpc, msg.author.name)
        if int(amount) >= user_balance:
            print('user %s not have enough to withdraw this amount (%s), balance = %s' % (
                msg.author.name, amount, user_balance))
            msg.reply('+/u/%s your balance is too low for this withdraw ' % msg.author.name)
        else:
            if utils.check_amount_valid(amount):
                receiver_address = split_message[4]
                try:
                    if crypto.send_to(rpc, sender_address, receiver_address, amount, True):
                        user_function.add_to_history(msg.author.name, sender_address, receiver_address, amount,
                                                     "withdraw")
                        msg.reply('Withdraw : ' + str(amount) + ' to ' + receiver_address)

                except:
                    traceback.print_exc()
            else:
                print('You must use valid amount')
                msg.reply('You must use valid amount')
    else:
        msg.reply('You need %s before' % linkRegister)


def tip_user(rpc, msg):
    print('An user mention detected ')
    split_message = msg.body.strip().split()
    tip_index = split_message.index('+/u/sodogetiptest')

    if split_message[tip_index] == '+/u/sodogetiptest' and split_message[tip_index + 2] == 'doge':
        amount = split_message[tip_index + 1]

        if utils.check_amount_valid(amount):
            parent_comment = msg.parent()
            if user_function.user_exist(msg.author.name):

                # check we have enough
                user_balance = crypto.get_user_balance(rpc, msg.author.name)
                if int(amount) >= user_balance:
                    print('user %s not have enough to tip this amount (%s), balance = %s' % (
                        msg.author.name, amount, user_balance))
                    msg.reply('+/u/%s your balance is too low for this tip ' % msg.author.name)
                else:

                    # check user have address before tip
                    if user_function.user_exist(parent_comment.author.name):
                        if crypto.tip_user(rpc, msg.author.name, parent_comment.author.name, amount):
                            user_function.add_to_history(msg.author.name, msg.author.name, parent_comment.author.name,
                                                         amount,
                                                         "tip")

                            print '%s tip %s to %s' % (msg.author.name, str(amount), parent_comment.author.name)
                            msg.reply('+/u/%s tip %s to %s' % (msg.author.name, str(amount),
                                                               parent_comment.author.name))
                    else:
                        user_function.save_unregistered_tip(msg.author.name, parent_comment.author.name, amount)
                        user_function.add_to_history(msg.author.name, msg.author.name, parent_comment.author.name,
                                                     amount,
                                                     "tip", False)
                        print('user %s not registered' % parent_comment.author.name)
                        msg.reply(
                            '+/u/%s need %s before can be tipped (tip saved during 3 day)' % (
                                parent_comment.author.name, linkRegister)
                        )
            else:
                msg.reply('You need %s before' % linkRegister)
        else:
            print('You must use valid amount')
            msg.reply('You must use valid amount')
