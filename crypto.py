import traceback

import time

import bot_logger
import config
import user_function
from config import bot_config


def get_user_balance(rpc, user):
    unspent_amounts = []

    address = user_function.get_user_address(user)
    # list_unspent = rpc.listunspent(1, 99999999999, [address])
    list_unspent_all = rpc.listunspent(0, 99999999999, [address])
    list_unspent = rpc.listunspent(0, 99999999999, [address])
    if len(list_unspent_all) == 0:
        return 0
    # in case of no un-spent transaction
    for i in range(len(list_unspent_all)):
        trans = rpc.decoderawtransaction(rpc.getrawtransaction(list_unspent_all[i]['txid']))
        for v_in in range(0, len(trans['vin']), 1):
            vin = rpc.decoderawtransaction(rpc.getrawtransaction(trans['vin'][v_in]['txid']))
            for item in range(0, len(vin['vout']), 1):
                for addr in range(0, len(vin['vout'][item]['scriptPubKey']['addresses']), 1):
                    if vin['vout'][item]['scriptPubKey']['addresses'][addr] in user_function.get_users().values():
                        continue
                    else:
                        list_unspent = rpc.listunspent(1, 99999999999, [address])
                        continue

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


def tip_user(rpc, sender_user, receiver_user, amount_tip):
    sender_address = user_function.get_user_address(sender_user)
    receiver_address = user_function.get_user_address(receiver_user)
    try:
        return send_to(rpc, sender_address, receiver_address, amount_tip)
    except:
        traceback.print_exc()


def send_to(rpc, sender_address, receiver_address, amount, take_fee_on_amount=False):
    bot_logger.logger.info("send %s to %s from %s" % (amount, sender_address, receiver_address))

    # list_unspent = rpc.listunspent(1, 99999999999, [address])
    list_unspent_all = rpc.listunspent(0, 99999999999, [address])
    list_unspent = rpc.listunspent(0, 99999999999, [address])
    if len(list_unspent_all) == 0:
        return 0
    # in case of no un-spent transaction
    for i in range(len(list_unspent_all)):
        trans = rpc.decoderawtransaction(rpc.getrawtransaction(list_unspent_all[i]['txid']))
        for v_in in range(0, len(trans['vin']), 1):
            vin = rpc.decoderawtransaction(rpc.getrawtransaction(trans['vin'][v_in]['txid']))
            for item in range(0, len(vin['vout']), 1):
                for addr in range(0, len(vin['vout'][item]['scriptPubKey']['addresses']), 1):
                    if vin['vout'][item]['scriptPubKey']['addresses'][addr] in user_function.get_users().values():
                        continue
                    else:
                        list_unspent = rpc.listunspent(1, 99999999999, [address])
                        continue

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
        if sum(unspent_amounts) > (float(amount) + float(fee)):
            break

    bot_logger.logger.debug("sum of unspend : " + str(sum(unspent_amounts)))
    bot_logger.logger.debug("fee : %s" % str(fee))
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

    rpc.walletpassphrase(config.wallet_passphrase, bot_config['timeout'])
    signed = rpc.signrawtransaction(raw_tx)
    rpc.walletlock()
    time.sleep(1)
    send = rpc.sendrawtransaction(signed['hex'])
    return send


def calculate_fee(nb_input, nb_out):
    size = nb_input * 180 + nb_out * 34 + 10
    # bot_logger.logger.debug("size of tx : %s" % size)

    fee_rate = float(bot_config['rate_fee'])
    fee = 1
    if size > 1000:
        fee = (size / 1000) * fee_rate

    return fee
