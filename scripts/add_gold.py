import argparse
# parse argument
import datetime

from tinydb import TinyDB

import config

parser = argparse.ArgumentParser(description='Refill Gold To Bot')
parser.add_argument('-n', help='Number of credits', required=True)
parser.add_argument('-c', help='Currency', required=True)
parser.add_argument('-p', help='Price of credits (total)', required=True)
args = parser.parse_args()

db = TinyDB(config.DATA_PATH + 'reddit_gold.json')
db.insert({
    "user_buyer": "",
    "quantity": args.n,
    "price": (float(args.n) / float(args.p)),
    "currency": args.c,
    "amount": "",
    "total_price": args.p,
    "usd_price": "",
    'tx_id': "",
    'status': "refill",
    'time': datetime.datetime.now().isoformat(),
})
db.close()
