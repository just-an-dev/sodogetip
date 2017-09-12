import multiprocessing
import time

import praw
from tinydb import TinyDB, Query

import bot_logger
import config
import crypto
import user_function
from models.history import HistoryStorage


class User(object):
    """Class to represent an user"""

    def __init__(self, user):
        self.username = user.lower()

        # address is activate address (only one address can be active)
        self.address = None

        if UserStorage.exist(self.username):
            self.address = UserStorage.get_user_address(self.username)

    def is_registered(self):
        # if user have address it's registered
        if self.address is not None:
            return True
        else:
            return False

    # get total of tips send to users who are not registered
    def get_balance_pending_tip(self):
        return user_function.get_balance_unregistered_tip(self.username)

    # user CONFIRMED balance with pending tips
    def get_balance_confirmed(self):
        # check if user have pending tips
        pending_tips = self.get_balance_pending_tip()
        bot_logger.logger.debug("pending_tips %s" % (str(pending_tips)))

        return crypto.get_user_confirmed_balance(self.address) - int(pending_tips)

    # user UN-CONFIRMED balance
    def get_balance_unconfirmed(self):
        return crypto.get_user_unconfirmed_balance(self.address)

    # generic balance function
    def get_balance(self, failover_time=None):
        balance = 0
        if self.is_registered():

            # get confirmed balance
            balance = float(self.get_balance_confirmed())

            # get unconfirmed balance come of bot
            balance += float(crypto.get_user_spendable_balance(self.address))

            if failover_time is not None and type(failover_time) is type(multiprocessing.Value):
                # if we call function without failover_time, we consider we are in safe mode
                if int(time.time()) > int(failover_time.value) + 86400:
                    # not in safe mode so add unconfirmed balance
                    balance += float(self.get_balance_unconfirmed())

        return balance

    def get_new_address(self, rpc=None):
        # create a new simple address
        if rpc is None:
            rpc = crypto.get_rpc()
        self.address = rpc.getnewaddress("reddit-%s" % self.username)

    def register(self):
        if self.address is None and UserStorage.exist(self.username) is not True:
            self.get_new_address()

        # register in users table
        UserStorage.add_address(self.username, self.address)

    def send_private_message(self, title, content):
        if self.reddit is None:
            self.reddit = praw.Reddit(config.bot_name)
        self.reddit.redditor(self.username).message(title, content)

    def get_history(self):
        return HistoryStorage.get_user_history(self.username)


class UserStorage:
    @staticmethod
    def add_address(username, address, active=True):
        db = TinyDB(config.user_file)
        table = db.table(username)

        # check if address not already exist
        user_db = Query()
        data = table.count(user_db.address == address)

        if data == 0:
            table.insert({"type": "simple", "address": address, "coin": "doge", "enable": False})

            if active is True:
                UserStorage.active_user_address(username, address)
        else:
            bot_logger.logger.error("address %s already registered for  %s " % (str(address), str(username)))

    @staticmethod
    def exist(username):
        db = TinyDB(config.user_file)
        user_list = db.tables()
        user_list.remove('_default')
        if unicode(username).lower() in map(unicode.lower, user_list):
            return True
        else:
            return False

    @classmethod
    def get_users(cls):
        db = TinyDB(config.user_file)
        user_list = db.tables()
        data = map(unicode.lower, user_list)
        data.remove('_default')
        return data

    @classmethod
    def get_all_users_address(cls):
        list_address = {}
        db = TinyDB(config.user_file)
        user_list = db.tables()
        data = map(unicode.lower, user_list)
        data.remove('_default')
        for account in data:
            list_address[account] = UserStorage.get_user_address(account)

        return list_address

    @classmethod
    def get_user_address(cls, username):
        if UserStorage.exist(username):
            db = TinyDB(config.user_file)
            table = db.table(username)
            user_db = Query()
            data = table.search(user_db.enable == True)
            if len(data) > 0:
                return data[0].get('address')
            else:
                # username not found
                return None
        else:
            bot_logger.logger.error("get address of un-registered user  %s " % (str(username)))

    @classmethod
    def active_user_address(cls, username, address):
        if UserStorage.exist(username):
            db = TinyDB(config.user_file)
            table = db.table(username)

            # check if address not already exist
            user_db = Query()
            data = table.count(user_db.address == address)

            if data == 1:
                # disable all other address
                enabled_address = table.search(user_db.enable == True)
                for item in enabled_address:
                    table.update({"enable": False}, eids=[item.eid])

                # enable only one
                table.update({"enable": True}, user_db.address == address)
            else:
                bot_logger.logger.error("active a not found address (%s)  of user  %s " % (str(address), str(username)))

        else:
            bot_logger.logger.error("active address of un-registered user  %s " % (str(username)))
