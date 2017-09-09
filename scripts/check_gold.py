#!/usr/bin/env python

import time

import praw

import config

operator_user = "just-an-dev"

while True:
    reddit = praw.Reddit(config.bot_config)
    if int(reddit.user.me().gold_creddits) < 1:
        print ("Send message to operator")

        reddit.redditor(operator_user).message('No more Gold', "No More Gold on Bot to Sell !! ")

    # each 30 minutes
    time.sleep(30 * 60)
