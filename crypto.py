import traceback

import bot_logger
import user_function


def get_user_balance(rpc, user):
    pending_tips = []
    unspent_amounts = []

    address = user_function.get_user_address(user)
    list_unspent = rpc.listunspent(1, 99999999999, [address])
    # in case of no un-spent transaction
    if len(list_unspent) == 0:
        return 0

    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])

    # check if user have pending tips
    list_tip_unregistered = user_function.get_unregistered_tip()
    for list_tip in list_tip_unregistered.values():
        for tip in list_tip:
            if tip['sender'] == user:
                pending_tips.append(int(tip['amount']))

    return int(sum(unspent_amounts) - sum(pending_tips))


def tip_user(rpc, sender_user, receiver_user, amount_tip):
    sender_address = user_function.get_user_address(sender_user)
    receiver_address = user_function.get_user_address(receiver_user)
    try:
        return send_to(rpc, sender_address, receiver_address, amount_tip)
    except:
        traceback.print_exc()


def send_to(rpc, sender_address, receiver_address, amount, take_fee_on_amount=False):
    bot_logger.logger.info("send %s to %s from %s" % (amount, receiver_address, sender_address))

    list_unspent = rpc.listunspent(1, 99999999999, [sender_address])

    unspent_list = []
    unspent_vout = []
    unspent_amounts = []

    for i in range(0, len(list_unspent), 1):
        unspent_list.append(list_unspent[i]['txid'])
        unspent_vout.append(list_unspent[i]['vout'])
        unspent_amounts.append(list_unspent[i]['amount'])
        if sum(unspent_amounts) > amount:
            break

    bot_logger.logger.debug("sum of unspend :" + str(sum(unspent_amounts)))

    raw_inputs = []
    for i in range(0, len(list_unspent), 1):
        tx = {
            "txid": str(list_unspent[i]['txid']),
            "vout": list_unspent[i]['vout']
        }
        raw_inputs.append(tx)

    bot_logger.logger.debug("raw input : %s" % raw_inputs)

    # fee = calculate_fee(raw_inputs, None)
    # logger.debug( "fee : %s" % str(fee))
    fee = 1

    if take_fee_on_amount:
        amount = (int(amount) - int(fee))

    return_amount = int(sum(unspent_amounts)) - int(amount) - int(fee)

    bot_logger.logger.debug("return amount : %s" % str(return_amount))

    if return_amount < 1:
        raw_addresses = {receiver_address: int(amount)}
    else:
        raw_addresses = {receiver_address: int(amount), sender_address: return_amount}

    bot_logger.logger.debug("raw addresses : %s" % raw_addresses)

    raw_tx = rpc.createrawtransaction(raw_inputs, raw_addresses)
    bot_logger.logger.debug("raw tx : %s" % raw_tx)

    bot_logger.logger.info('send %s Doge form %s to %s ' % (str(amount), receiver_address, receiver_address))

    signed = rpc.signrawtransaction(raw_tx)
    send = rpc.sendrawtransaction(signed['hex'])
    return send


def calculate_fee(raw_inputs, raw_addresses):
    nb_input = len(raw_inputs)
    # nb_out = len(raw_addresses)
    nb_out = 2
    fee = nb_input * 180 + nb_out * 34 + 10
    return fee
