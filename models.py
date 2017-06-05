import re


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


class Action(object):
    """Class to represent an action made by user"""
    def __init__(self):
        self.action = None
        self.tip = None
