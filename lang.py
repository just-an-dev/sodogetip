#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

import config

link_register = "https://www.reddit.com/message/compose?to=" + config.bot_name + "&subject=\%2Bregister&message=\%2Bregister"
link_help = "https://www.reddit.com/message/compose?to=" + config.bot_name + "&subject=%2Bhelp&message=%2Bhelp"
link_withdraw = "https://www.reddit.com/message/compose?to=" + config.bot_name + "&subject=%2Bwithdraw&message=%2Bwithdraw%20AMOUNT%20doge%20to%20ADDRESS"
link_history = "https://www.reddit.com/message/compose?to=" + config.bot_name + "&subject=%2Bhistory&message=%2Bhistory"
link_info = "https://www.reddit.com/message/compose?to=" + config.bot_name + "&subject=%2Binfo&message=%2Binfo"
link_balance = "https://www.reddit.com/message/compose?to=" + config.bot_name + "&subject=%2Bbalance&message=%2Bbalance"

link_gold = "https://www.reddit.com/gold/about"
link_gold_buy = "https://www.reddit.com/message/compose?to=" + config.bot_name + "&subject=%2Bgold&message=buy"

message_register_success = ("Hello /u/{{ username }}! Your account is now registered and ready to tip Dogecoins :)" \
                            "\n\nYour wallet address is: {{ address }}" \
                            "\n\nThis bot is \"on chain\" so when you tip some __mining fee are added__ ! " \
                            "\n\nWondering how to get tipped Dogecoins? Participate in /r/dogecoin!" \
                            "\n\nIf you need help using me (such as tipping people), you can send me a +help message [here](" + link_help + ") to receive a getting started guide." \
                                                                                                                                            "\n\n__DID YOU KNOW?:__ Unlike other tip bots, this one is non-profit and maintained by the community. Checkmate!")

message_need_register = ("Hello /u/{{ username }}! You need to register an account before you can use me." \
                         "\n\nTo register an account:" \
                         "\n\n1. [Click here](" + link_register + ") to send a pre-filled +register message" \
                                                                  "\n\n2. Click the \"Send\" button" \
                                                                  "\n\n3. Receive the successful register message" \
                                                                  "\n\nThe successful register message will contain your Dogecoin address to your tipping account.")

message_invalid_amount = "__^[such ^error]__: ^The ^tip ^amount ^must ^be ^at ^least ^1 ^doge. ^[[help]](" + link_help + ")"
message_invalid_currency = "__^[such ^error]__: ^The ^tip ^currency ^must ^be ^doge. ^[[help]](" + link_help + ")"
message_balance_low_tip = (
    "__^[such ^error]__: ^/u/{{ username }}\'s ^balance ^is ^too ^low ^for ^this ^tip ^[[help]](" + link_help + ")")
message_balance_pending_tip = (
    "__^[such ^error]__: ^/u/{{ username }}\'s ^balance ^must ^wait ^for ^pending ^tips ^to ^be ^confirmed ^before ^sending ^this ^tip ^amount ^[[help]](" + link_help + ")")
message_already_registered = "You are already registered!"
message_balance_low_withdraw = (
    "Hello /u/{{ username }}! It seems your balance of __Ð{{ user_balance }}__ is too low for this withdraw amount of __Ð{{ amount }}__." \
    "\n\n[Want to try again?](" + link_withdraw + ")")

message_account_details = "\n\nHere are your account details /u/{{ username }}!" \
                          "\n\n^very ^info | &nbsp;" \
                          "\n---|---" \
                          "\n^Your ^balance | ^{{ spendable_balance }} ^doge ^(${{ spendable_value_usd }})" \
                          "\n^Your ^pending ^balance | ^{{ pending_balance }} ^doge ^(${{ pending_value_usd }})" \
                          "\n^Tips ^to ^unregistered ^users | ^{{ pending_tips }} ^doge ^(${{ pending_tips_value_usd}})" \
                          "\n^Deposit ^address | ^{{ address }}" \
                          "\n^Withdraw | ^[+withdraw](" + link_withdraw + ")" \
                                                                          "\n\n__ATTENTION:__ This bot is \"on chain\" so for every tip you make, you'll pay a small fee (typically 1 DOGE)!"

message_not_supported = "__^[such ^error]__: ^That ^is ^currently ^not ^supported! ^[[help]](" + link_help + ")"

message_history = ("Hello /u/{{ username }}! Here is your transaction history: \n\n")
message_tip = (
    "__^[wow ^so ^verify]__: ^/u/{{ sender }} ^-> ^/u/{{ receiver }} ^__Ð{{ amount }}__ ^__doge__ ^__(${{ value_usd }})__ ^[[help]](" + link_help + ")  ^[[transaction]](https://chain.so/tx/DOGE/{{ txid }})")
message_withdraw = (
    "__^[wow ^so ^verify]__: ^/u/{{ username }} ^-> ^{{ receiver_address }} ^__Ð{{ amount }}__ ^__doge__ ^__(${{ value_usd }})__ ^[[help]](" + link_help + ")")
message_withdraw_to_self = ("__^[such ^error]__: ^You ^cannot ^withdraw ^to ^your ^own ^bot ^address")
message_footer = ("\n\n*****" \
                  "\n\nNew to Dogecoin or " + config.bot_name + "? Ask the community any questions on /r/dogecoin!" \
                                                                "\n\n^quick ^commands |&nbsp;" \
                                                                "\n---|---" \
                                                                "\n^Past ^tips|^[+history](" + link_history + ")" \
                                                                                                              "\n^Get ^account ^details|^[+info](" + link_info + ")" \
                                                                                                                                                                 "\n^Balance|^[+balance](" + link_balance + ")" \
                                                                                                                                                                                                            "\n^Help ^me!|^[+help](" + link_help + ")" \
                                                                                                                                                                                                                                                   "\n\n__PROTIP:__ An example tip would be: +/u/" + config.bot_name + " 100 doge")

message_help = (
    "Welcome to Dogecoin and " + config.bot_name + "!\n\nThe community is extremely important to us, and we\'re always happy to see new faces and help people like you get excited about the most fun and social coin out there :)\n\nTo learn more about Dogecoin and experience our friendly community, check out the /r/dogecoin subreddit. Don't worry, we don't bite (unlike real-life shibes).\n\nUnlike other tipping services," + config.bot_name + " is built on an \"on chain\" platform. This means every tip is verified by the secure Dogecoin network and publically viewable on its database of transactions (called a blockchain) for a small fee (typically 1 DOGE).\n\nThis is your wallet address: {{ address }}\n\nHow to use " + config.bot_name + ":\n\nSend someone a Dogecoin tip by commenting or replying: +/u/" + config.bot_name + " AMOUNT doge. Replace AMOUNT with an amount of Dogecoins (ex. 100 to tip 100 DOGE).\n\n[+history](" + link_history + ") - view your transaction history (includes tips and withdraws)\n\n[+info](" + link_info + ") or [+balance](" + link_balance + ") - view your Dogecoin balance on /u/" + config.bot_name + "\n\n[+withdraw](" + link_withdraw + ") - withdraw Dogecoins from your /u/" + config.bot_name + " balance into a separate Dogecoin address")

message_recipient_register = (
    "__^[such ^error]__: ^/u/{{ username }} ^needs ^to ^[register](" + link_register + ") ^before ^receiving ^any ^tips. __^\(this ^tip ^has ^been ^saved ^for ^3 ^days)__ ^[[help]](" + link_help + ")")
message_recipient_need_register_title = (
    "Someone sent you a Dogecoin tip of Ð{{ amount }}, and you need to register to receive it!")
message_recipient_need_register_message = (
    "Hello /u/{{ username }}! You need to register an account before you can receive __{{ sender }}\'s__ Dogecoin tip of __Ð{{ amount }} doge (${{ value_usd }})__." \
    "\n\nTo register an account:" \
    "\n\n1. [Click here](" + link_register + ") to send a pre-filled +register message" \
                                             "\n\n2. Click the \"Send\" button" \
                                             "\n\n3. Receive the successful register message" \
                                             "\n\nThe successful register message will contain your Dogecoin address to your tipping account.")
message_recipient_self = ("__^[such ^error]__: ^You ^cannot ^send ^yourself ^a ^tip")

# Gold Message

message_buy_gold = "You can buy an reddit [gold](" + link_gold + "), price is {{ price }} for one month.\n\n " \
                                                                 "To buy send a [message](" + link_gold_buy + ") to bot with subject +gold an content 'buy' \n\n" \
                                                                                                              "The amount will be deducted on your wallet.\n\n" \
                                                                                                              "There are {{ gold_credit }} credits remaining for sale\n\n" \
                                                                                                              "The price is bit over than reddit price because it add fee to bitcoin exchange, support hosting cost, etc .."

message_gold_no_more = "Sorry no more gold tickets to sell"
message_buy_gold_error = "Error during buy of gold credits"
message_buy_gold_success = "Thanks to buy reddit gold via bot and support hosting cost, all coffee for developpers, etc ..."

message_gold_no_enough_doge = "Sorry it seems your confirmed balance is too low"
