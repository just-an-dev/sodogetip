import re
from random import randint

import crypto
import user_function
import utils


class Tip(object):
    """Class to represent a tip of user"""

    def __init__(self):
        self.receiver = None
        self.amount = None
        self.verify = False
        self.sender = None
        self.finish = False
        self.tx_id = None

    def parse_message(self, message_to_parse):
        p = re.compile('(\+\/u\/sodogetiptest)\s?(@?[0-9a-zA-Z]+)?\s+(\d+|[0-9a-zA-Z]+)\s(doge)\s(verify)?')
        m = p.search(message_to_parse.lower().strip())
        # Group 1 is +/u/sodogetiptest
        # Group 2 is either blank(tip to the commentor), an address, or a user
        self.receiver = m.group(1)
        # Group 3 is the tip amount in integers(ex.  100) or a word(ex.roll)
        self.amount = m.group(3)
        # Group 4 is doge
        # Group 5 is either blank(no verify message) or verify(verify message)
        self.verify = True if (m.group(5) == "verify") else False

        # to support any type of randomXXX amount
        if 'random' in self.amount and utils.check_amount_valid(self.amount[:6]):
            self.amount = randint(1, int(self.amount[:6]))


class User(object):
    """Class to represent an user"""

    def __init__(self, user):
        self.username = user
        self.address = None

        if user_function.user_exist(self.username):
            self.address = user_function.get_user_address(self.username)
