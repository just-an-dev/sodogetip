import datetime
import random
import re
from tinydb import TinyDB, Query

import bot_logger
import config
import crypto
import user_function
import utils


class Tip(object):
    """Class to represent a tip of user"""

    def __init__(self):
        self.receiver = None
        self.amount = None
        self.verify = False
        self.currency = None
        self.sender = None
        self.finish = False
        self.status = None
        self.tx_id = None

        self.id = random.randint(0, 99999999)
        # reddit message id
        self.message_fullname = None,
        self.time = datetime.datetime.now().isoformat()

    # you need to set send before using this function
    def parse_message(self, message_to_parse, rpc=None):
        if rpc is None:
            # init rpc to validate address
            rpc = crypto.get_rpc()

        p = re.compile(
            '(\+\/u\/' + config.bot_name + ')\s?(@?[0-9a-zA-Z-_\/\+]+)?\s+(\d+|[0-9a-zA-Z,.]+)\s(doge)\s?(verify)?',
            re.IGNORECASE)
        m = p.search(message_to_parse.strip())
        # Group 1 is +/u/sodogetiptest
        # Group 2 is either blank(tip to the commentor), an address, or a user
        self.receiver = m.group(2)
        # Group 3 is the tip amount in integers(ex.  100) or a word(ex.roll)
        self.amount = m.group(3).replace(',', '.')
        # Group 4 is doge
        self.currency = m.group(4)
        # Group 5 is either blank(no verify message) or verify(verify message)
        self.verify = True if (m.group(5) == "verify") else False

        if self.receiver is not None:
            # to support send tip to username
            if '+/u/' in self.receiver:
                self.receiver = User(self.receiver[4:])
            elif '/u/' in self.receiver:
                self.receiver = User(self.receiver[3:])
            elif 'u/' in self.receiver:
                self.receiver = User(self.receiver[2:])
            elif '@' in self.receiver:
                self.receiver = User(self.receiver[1:])
            # to support send tip to an address
            elif len(self.receiver) == 34 and rpc.validateaddress(self.receiver)['isvalid']:
                address = self.receiver
                bot_logger.logger.info("Send an tip to address")
                self.receiver = User("address-" + address)
                self.receiver.username = ("address-" + address)
                self.receiver.address = address

        # to support any type of randomXXX amount
        if 'random' in self.amount and utils.check_amount_valid(self.amount[6:]):
            self.amount = random.randint(1, int(self.amount[6:]))

        # here amount is numeric, make magic to support not whole tips
        if utils.check_amount_valid(self.amount):
            self.amount = round(float(self.amount) - 0.5)

        # if amount is all, get balance
        if self.amount == 'all':
            # get user balance
            self.amount = self.sender.get_balance()

        bot_logger.logger.debug("isinstance self.amount = %s" % str(isinstance(self.amount, str)))
        bot_logger.logger.debug("type self.amount = %s" % str(type(self.amount)))

        if type(self.amount) is unicode or type(self.amount) is str:
            bot_logger.logger.debug("self.amount is str")
            if self.amount == "roll":
                self.amount = random.randint(1, 6)

            elif self.amount == "flip":
                self.amount = random.randint(1, 2)

            elif self.amount in config.tip_keyword.keys():
                self.amount = config.tip_keyword[self.amount]

        bot_logger.logger.debug("self.amount = %s" % str(self.amount))

        # if tip is over 1000 doge set verify
        if float(self.amount) >= float(1000):
            self.verify = True

    def set_sender(self, sender_username):
        self.sender = User(sender_username)

    def set_receiver(self, receiver_username):
        # update only if previous is blank (other case it will be set in parse_message)
        if self.receiver is None:
            self.receiver = User(receiver_username)

    def get_value_usd(self):
        return utils.get_coin_value(self.amount, self.currency)

    def create_from_array(self, arr_tip):
        # import user
        self.receiver = User(arr_tip['receiver'])
        self.sender = User(arr_tip['sender'])
        del arr_tip['receiver']
        del arr_tip['sender']

        for key in arr_tip.keys():
            setattr(self, key, arr_tip[key])

        return self

    def is_expired(self):
        limit_date = datetime.datetime.now() - datetime.timedelta(days=3)

        if type(self.time) is str:
            return limit_date > datetime.datetime.strptime(self.time, '%Y-%m-%dT%H:%M:%S.%f')

        if type(self.time) is datetime.datetime:
            return limit_date > self.time

        if type(self.time) is unicode:
            return limit_date > datetime.datetime.strptime(self.time, '%Y-%m-%dT%H:%M:%S.%f')


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

            if failover_time is not None:
                # if we call function without failover_time, we consider we are in safe mode
                if datetime.time.time() > int(failover_time.value) + 86400:
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
                active_user_address(username, address)
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
            return data[0].get('address')
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

            if data == 0:
                # disable all other address
                table.update(set("enable", False))

                # enable only one
                table.update(set("enable", True), user_db.address == address)
            else:
                bot_logger.logger.error("active a not found address (%s)  of user  %s " % (str(address), str(username)))

        else:
            bot_logger.logger.error("active address of un-registered user  %s " % (str(username)))


class VanityGenRequest(object):
    """Class to represent an user"""

    def __init__(self, user, vanity):
        self.user = User(user)
        self.pattern = None
        self.difficulty = None
        self.address = None
        self.privkey = None

        # to check if we move funds of user
        self.use = None

    def parse_message(self, message_to_parse, rpc=None):
        split_message = message_to_parse.split()

        # parse message like : +vanity use Dpatern
        donate_index = split_message.index('+vanity')
        use_address = split_message[donate_index + 1]
        pattern = split_message[donate_index + 2]

        if use_address == "use":
            self.use = True
        if use_address == "not-use":
            self.use = False

            # check patern is ok

    def save_resquest(self):
        pass

    def create_from_array(self, arr_vanity):
        self.user = User(arr_vanity['user'])
        del arr_vanity['user']

        for key in arr_vanity.keys():
            setattr(self, key, arr_vanity[key])

    def generate(self):
        # parse output
        address_generated = ""

    def move_funds(self, tx_queue, failover_time):
        if self.use is True:
            amount = self.user.get_balance()
            if crypto.tip_user(self.user.address, self.address, amount, tx_queue, failover_time):
                # update user storage file
                UserStorage.add_address(self.user.username, self.address)

                # Todo : update history of user

    def import_address(self):
        rpc = crypto.get_rpc()
        rpc.importprivkey(self.privkey, "reddit-vanity-" + self.user.username, false)

        # on import success clean key from memory
        self.privkey = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        self.privkey = None
