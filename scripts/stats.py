#!/usr/bin/env python

# list of users
import argparse
import datetime
from os import listdir
from os.path import isfile, join

import praw
from tinydb import TinyDB

import config
import models

# user registered
list_of_user = {'all': []}

# user not registered
list_of_user_miss = {'all': []}

# high tips
high_tip = {'all': {}}
high_tip['all']['amount'] = 0

# Average tips
average_tip = {'all': []}

# parse argument
parser = argparse.ArgumentParser(description='Bot Monthly stats')
parser.add_argument('-f', help='Date formater for analyse', type=str, dest='formater', default="%Y-%m")
parser.add_argument('--gold', help='Gold', type=bool, dest='gold', default=False)
parser.add_argument('--debug', help='Debug', type=bool, dest='debug', default=False)
args = parser.parse_args()

if args.gold:
    print "\n\n Gold Creddit :"
    reddit = praw.Reddit(config.bot_config)
    print "Current gold credit  => " + str(reddit.user.me().gold_creddits)
else:
    print "Formater used for analysis is " + args.formater

    # check users history, list file in path
    history_path = config.history_path
    only_files = [f for f in listdir(history_path) if isfile(join(history_path, f))]

    for username in only_files:
        clean_user = username.replace('.json', '')

        u = models.User(clean_user)

        db = TinyDB(config.history_path + clean_user + '.json')
        data_histo = db.all()
        for row in data_histo:

            date_check = datetime.datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%S.%f')
            key = date_check.strftime(args.formater)

            # Compute registration
            if u.is_registered():
                if clean_user not in list_of_user['all']:
                    list_of_user['all'].append(clean_user)

                if key not in list_of_user.keys():
                    list_of_user[key] = []

                if clean_user not in list_of_user[key]:
                    list_of_user[key].append(clean_user)
            else:
                if clean_user not in list_of_user_miss['all']:
                    list_of_user_miss['all'].append(clean_user)

                if key not in list_of_user_miss.keys():
                    list_of_user_miss[key] = []

                if clean_user not in list_of_user_miss[key]:
                    list_of_user_miss[key].append(clean_user)

            # Computer tips stats
            if row['action'] == "tip send":
                # High Tip
                if float(row['amount']) > float(high_tip['all']['amount']):
                    high_tip['all'] = row

                if key not in high_tip.keys():
                    high_tip[key] = {}
                    high_tip[key]['amount'] = 0

                if float(row['amount']) > float(high_tip[key]['amount']):
                    high_tip[key] = row

                # Average Tip
                average_tip['all'].append(row['amount'])

                if key not in average_tip.keys():
                    average_tip[key] = []

                average_tip[key].append(row['amount'])

    print "\n\n Registration :"
    for (month, item) in sorted(list_of_user.items(), reverse=True):
        print month + " => " + str(len(item))

    print "\n\n Missing Registration :"
    for (month, item) in sorted(list_of_user_miss.items(), reverse=True):
        print month + " => " + str(len(item))

    print "\n\n High Tip :"
    for (month, item) in sorted(high_tip.items(), reverse=True):
        if args.debug:
            print month + " => " + str(item)
        else:
            print month + " => " + item['sender'] + " send " + str(item['amount']) + " to " + item['receiver']

    print "\n\n Average Tip :"
    for (month, item) in sorted(average_tip.items(), reverse=True):
        print month + " => " + str(sum(item) / len(item))

    print "\n\n Number of Tip :"
    for (month, item) in sorted(average_tip.items(), reverse=True):
        print month + " => " + str(len(item))

    print "\n\n Total amount of Tip :"
    for (month, item) in sorted(average_tip.items(), reverse=True):
        print month + " => " + str(sum(item))
