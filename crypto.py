import getpass
import time
import traceback

import bot_logger
import user_function
from config import bot_config


def init_passphrase():
    # enter user passphrase
    global wallet_passphrase
    wallet_passphrase = getpass.getpass("wallet passphrase : ")


def get_user_spendable_balance(rpc, user):
    # spendable_balance is the confirmed balance and the unconfirmed balance of
    # transactions that the bot has generated, but not the unconfirmed balance of
    # transactions originating from a wallet address that does not belong to the bot
    unspent_amounts = []
    address = user_function.get_user_address(user)
    list_unspent = rpc.listunspent(0, 0, [address])

    # in case of no un-spent transaction
    if len(list_unspent) == 0:
        return 0

    for i in range(0, len(list_unspent), 1):
        trans = rpc.decoderawtransaction(rpc.getrawtransaction(list_unspent[i]['txid']))
        # for v_in in range(0,len(trans['vin']),1):
        vin = rpc.decoderawtransaction(rpc.getrawtransaction(trans['vin'][0]['txid']))
        if vin['vout'][0]['scriptPubKey']['addresses'][0] in user_function.get_users().values():
            unspent_amounts.append(list_unspent[i]['amount'])

            # for item in range(0,len(vin['vout']),1):
            # for addr in range(0,len(vin['vout'][item]['scriptPubKey']['addresses']),1):
            # if vin['vout'][item]['scriptPubKey']['addresses'][addr] in user_function.get_users().values():
            # continue
            # else:
            # list_unspent = rpc.listunspent(1, 99999999999, [address])
            # continue

            # for i in range(0, len(list_unspent), 1):
            # unspent_amounts.append(list_unspent[i]['amount'])

    bot_logger.logger.debug("unspent_amounts %s" % (str(sum(unspent_amounts))))

    current_balance = rpc.getbalance("reddit-%s" % user)
    bot_logger.logger.debug("current_balance %s" % (str(int(current_balance))))

    if int(current_balance) != int(sum(unspent_amounts)):
        bot_logger.logger.warn("maybe an error !")

    # check if user have pending tips
    pending_tips = user_function.get_balance_unregistered_tip(user)

    bot_logger.logger.debug("pending_tips %s" % (str(pending_tips)))

    return int(sum(unspent_amounts) - int(pending_tips))


def get_user_confirmed_balance(rpc, user):
    unspent_amounts = []

    address = user_function.get_user_address(user)
    list_unspent = rpc.listunspent(1, 99999999999, [address])
    # in case of no un-spent transaction
    if len(list_unspent) == 0:
        return 0

    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])

    bot_logger.logger.debug("unspent_amounts %s" % (str(sum(unspent_amounts))))

    current_balance = rpc.getbalance("reddit-%s" % user)
    bot_logger.logger.debug("current_balance %s" % (str(int(current_balance))))

    if int(current_balance) != int(sum(unspent_amounts)):
        bot_logger.logger.warn("maybe an error !")

    # check if user have pending tips
    pending_tips = user_function.get_balance_unregistered_tip(user)

    bot_logger.logger.debug("pending_tips %s" % (str(pending_tips)))

    return int(sum(unspent_amounts) - int(pending_tips))


def get_user_unconfirmed_balance(rpc, user):
    unspent_amounts = []

    address = user_function.get_user_address(user)
    list_unspent = rpc.listunspent(0, 0, [address])
    # in case of no unconfirmed transactions
    if len(list_unspent) == 0:
        return 0

    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])

    bot_logger.logger.debug("unconfirmed_amounts %s" % (str(sum(unspent_amounts))))

    unconfirmed_balance = rpc.getbalance("reddit-%s" % user)
    bot_logger.logger.debug("unconfirmed_balance %s" % (str(int(unconfirmed_balance))))

    return int(sum(unspent_amounts))


def tip_user(rpc, sender_user, receiver_user, amount_tip):
    sender_address = user_function.get_user_address(sender_user)
    receiver_address = user_function.get_user_address(receiver_user)
    try:
        return send_to(rpc, sender_address, receiver_address, amount_tip)
    except:
        traceback.print_exc()


def send_to(rpc, sender_address, receiver_address, amount, take_fee_on_amount=False):
    bot_logger.logger.info("send %s to %s from %s" % (amount, sender_address, receiver_address))

    list_unspent = rpc.listunspent(1, 99999999999, [sender_address])

    unspent_amounts = []
    raw_inputs = []
    fee = 1

    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])
        # check if we have enough tx
        tx = {
            "txid": str(list_unspent[i]['txid']),
            "vout": list_unspent[i]['vout']
        }
        raw_inputs.append(tx)
        fee = calculate_fee(len(raw_inputs), 2)
        if sum(unspent_amounts) > (float(amount) + float(fee)) and (calculate_size(len(raw_inputs), 2) >= 750):
            break

    list_unspent = rpc.listunspent(0, 0, [sender_address])

    for i in range(0, len(list_unspent), 1):
        trans = rpc.decoderawtransaction(rpc.getrawtransaction(list_unspent[i]['txid']))
        vin = rpc.decoderawtransaction(rpc.getrawtransaction(trans['vin'][0]['txid']))
        if vin['vout'][0]['scriptPubKey']['addresses'][0] in user_function.get_users().values():
            unspent_amounts.append(list_unspent[i]['amount'])
            tx = {
                "txid": str(list_unspent[i]['txid']),
                "vout": list_unspent[i]['vout']
            }
            raw_inputs.append(tx)
            fee = calculate_fee(len(raw_inputs), 2)
            if sum(unspent_amounts) > (float(amount) + float(fee)):
                break

    bot_logger.logger.debug("sum of unspend : " + str(sum(unspent_amounts)))
    bot_logger.logger.debug("fee : %s" % str(fee))
    bot_logger.logger.debug("size : %s" % str(calculate_size(len(raw_inputs), 2)))
    bot_logger.logger.debug("raw input : %s" % raw_inputs)

    if take_fee_on_amount:
        return_amount = int(sum(unspent_amounts)) - int(int(amount) - int(fee))
    else:
        return_amount = int(sum(unspent_amounts)) - int(amount) - int(fee)

    bot_logger.logger.debug("return amount : %s" % str(return_amount))

    if int(return_amount) < 1:
        raw_addresses = {receiver_address: int(amount)}
    else:
        # when consolidate tx
        if receiver_address == sender_address:
            raw_addresses = {receiver_address: int(int(amount) - int(fee))}
        else:
            raw_addresses = {receiver_address: int(amount), sender_address: int(return_amount)}

    bot_logger.logger.debug("raw addresses : %s" % raw_addresses)

    raw_tx = rpc.createrawtransaction(raw_inputs, raw_addresses)
    bot_logger.logger.debug("raw tx : %s" % raw_tx)

    bot_logger.logger.info('send %s Doge form %s to %s ' % (str(amount), receiver_address, receiver_address))

    rpc.walletpassphrase(wallet_passphrase, int(bot_config['timeout']))
    signed = rpc.signrawtransaction(raw_tx)
    rpc.walletlock()
    time.sleep(1)
    send = rpc.sendrawtransaction(signed['hex'])
    return send


def calculate_fee(nb_input, nb_out):
    size = calculate_size(nb_input, nb_out)
    # bot_logger.logger.debug("size of tx : %s" % size)

    fee_rate = float(bot_config['rate_fee'])
    fee = 1
    if size > 1000:
        fee = (size / 1000) * fee_rate

    return fee


def calculate_size(nb_input, nb_out):
    return nb_input * 180 + nb_out * 34 + 10
