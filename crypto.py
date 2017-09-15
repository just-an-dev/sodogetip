import datetime
import getpass
import logging
import time
import traceback

from bitcoinrpc.authproxy import AuthServiceProxy

import bot_logger
import config
import models


def get_rpc():
    return AuthServiceProxy("http://%s:%s@%s:%s" % (
        config.rpc_config['doge_rpc_username'], config.rpc_config['doge_rpc_password'],
        config.rpc_config['doge_rpc_host'],
        config.rpc_config['doge_rpc_port']), timeout=config.rpc_config['timeout'])


def backup_wallet():
    rpc = get_rpc()
    rpc.backupwallet(
        config.backup_wallet_path + "backup_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + ".dat")


def init_passphrase():
    # enter user passphrase
    global wallet_passphrase
    wallet_passphrase = getpass.getpass("wallet passphrase : ")


def check_passphrase():
    rpc = get_rpc()

    logging.disable(logging.DEBUG)
    rpc.walletpassphrase(wallet_passphrase, int(config.rpc_config['timeout']))
    logging.disable(logging.NOTSET)

    # let some daemon time to unlock wallet
    time.sleep(1)

    # check
    wallet_info = rpc.getwalletinfo()
    if wallet_info['unlocked_until'] < time.time():
        exit()

    rpc.walletlock()

def get_user_spendable_balance(address, rpc=None):
    if rpc is None:
        rpc = get_rpc()

    # spendable_amounts is the unconfirmed balance of transactions that the bot has generated,
    # but not the unconfirmed balance of transactions originating from
    # a wallet address that does not belong to the bot

    # TODO : check if confirm tx are in list when using 0 0

    spendable_amounts = []
    list_unspent = rpc.listunspent(0, 0, [address])

    # in case of no un-spent transaction
    if len(list_unspent) == 0:
        return 0

    for i in range(0, len(list_unspent), 1):
        trans = rpc.decoderawtransaction(rpc.getrawtransaction(list_unspent[i]['txid']))
        # for v_in in range(0,len(trans['vin']),1):
        vin = rpc.decoderawtransaction(rpc.getrawtransaction(trans['vin'][0]['txid']))
        if vin['vout'][0]['scriptPubKey']['addresses'][0] in models.UserStorage.get_all_users_address().values():
            spendable_amounts.append(list_unspent[i]['amount'])

    bot_logger.logger.debug("unspent_amounts %s" % (str(sum(spendable_amounts))))

    return int(sum(spendable_amounts))


def get_user_confirmed_balance(address):
    rpc = get_rpc()

    unspent_amounts = []

    list_unspent = rpc.listunspent(1, 99999999999, [address])

    # in case of no un-spent transaction
    if len(list_unspent) == 0:
        return 0

    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])

    bot_logger.logger.debug("unspent_amounts %s" % (str(sum(unspent_amounts))))

    return int(sum(unspent_amounts))


def get_user_unconfirmed_balance(address):
    rpc = get_rpc()

    unspent_amounts = []
    list_unspent = rpc.listunspent(0, 0, [address])

    # in case of no unconfirmed transactions
    if len(list_unspent) == 0:
        return 0

    for i in range(0, len(list_unspent), 1):
        unspent_amounts.append(list_unspent[i]['amount'])

    bot_logger.logger.debug("unconfirmed_amounts %s" % (str(sum(unspent_amounts))))

    return int(sum(unspent_amounts))


def tip_user(sender_address, receiver_address, amount_tip, tx_queue, failover_time):
    bot_logger.logger.debug("failover_time : %s " % (str(failover_time.value)))

    if time.time() > int(failover_time.value) + 86400:
        bot_logger.logger.info("tip send in normal mode")
        try:
            return send_to(None, sender_address, receiver_address, amount_tip, False, tx_queue)
        except:
            traceback.print_exc()
    else:
        bot_logger.logger.info("tip send in safe mode")
        try:
            return send_to_failover(None, sender_address, receiver_address, amount_tip, False, tx_queue)
        except:
            traceback.print_exc()


def send_to(rpc, sender_address, receiver_address, amount, take_fee_on_amount=False, tx_queue=None):
    if rpc is None:
        rpc = get_rpc()

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
        if vin['vout'][0]['scriptPubKey']['addresses'][0] in models.UserStorage.get_all_users_address().values():
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

    logging.disable(logging.DEBUG)
    rpc.walletpassphrase(wallet_passphrase, int(config.rpc_config['timeout']))
    logging.disable(logging.NOTSET)

    signed = rpc.signrawtransaction(raw_tx)
    rpc.walletlock()
    send = rpc.sendrawtransaction(signed['hex'])

    # add tx id in queue for double spend check
    if tx_queue is not None:
        time.sleep(4)
        tx_queue.put(send)

    return send


def send_to_failover(rpc, sender_address, receiver_address, amount, take_fee_on_amount=False, tx_queue=None):
    if rpc is None:
        rpc = get_rpc()

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

    logging.disable(logging.DEBUG)
    rpc.walletpassphrase(wallet_passphrase, int(config.rpc_config['timeout']))
    logging.disable(logging.NOTSET)

    signed = rpc.signrawtransaction(raw_tx)
    rpc.walletlock()
    send = rpc.sendrawtransaction(signed['hex'])

    # add tx id in queue for double spend check
    if tx_queue is not None:
        time.sleep(4)
        tx_queue.put(send)

    return send


def calculate_fee(nb_input, nb_out):
    size = calculate_size(nb_input, nb_out)
    # bot_logger.logger.debug("size of tx : %s" % size)

    fee_rate = float(config.rate_fee)
    fee = 1
    if size > 1000:
        fee = (size / 1000) * fee_rate

    return fee


def calculate_size(nb_input, nb_out):
    return nb_input * 180 + nb_out * 34 + 10
