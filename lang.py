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

message_register_success = ("Hello /u/{{ username }}! Your account is now registered and ready to tip Dogecoins :)" \
                           "\n\nYour wallet address is: {{ address }}" \
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
message_balance_low_tip = ("__^[such ^error]__: ^/u/{{ username }}\'s ^balance ^is ^too ^low ^for ^this ^tip ^[[help]](" + link_help + ")")
message_balance_pending_tip = ("__^[such ^error]__: ^/u/{{ username }}\'s ^balance ^must ^wait ^for ^pending ^tips ^to ^be ^confirmed ^before ^sending ^this ^tip ^amount ^[[help]](" + link_help + ")")
message_already_registered = "You are already registered!"
message_balance_low_withdraw = ("Hello /u/{{ username }}! It seems your balance of __Ð{{ user_balance }}__ is too low for this withdraw amount of __Ð{{ amount }}__." \
                                        "\n\n[Want to try again?](" + link_withdraw + ")")

message_account_details = ("\n\nHere are your account details /u/{{ username }}!" \
                            "\n\n^very ^info | &nbsp;" \
                            "\n---|---" \
                            "\n^Your ^balance | ^{{ balance }} ^doge ^(${{ balance_value_usd }})" \
                            "\n^Your ^pending ^balance | ^{{ pendingbalance }} ^doge ^(${{ pending_value_usd }})"
                            "\n^Your ^spendable ^balance | ^{{ spendablebalance }} ^doge (${{ spendable_value_usd }})"
                            "\n^Deposit ^address | ^{{ address }}" \
                            "\n^Withdraw | ^[+withdraw](" + link_withdraw + ")")
message_not_supported = "__^[such ^error]__: ^That ^is ^currently ^not ^supported! ^[[help]](" + link_help + ")"
message_balance = ("Hello /u/{{ username }}!" \
                           "\n\nYour confirmed balance is: {{ balance }} (${{ balance_value_usd }})" \
                           "\n\nYour unconfirmed balance is: {{ pendingbalance }} (${{ pending_value_usd }})"
                           "\n\nYour spendable balance is: {{ spendablebalance }} (${{ spendable_value_usd}})")
message_history = ("Hello /u/{{ username }}! Here is your transaction history: \n\n")
message_tip = ("__^[wow ^so ^verify]__: ^/u/{{ sender }} ^-> ^/u/{{ receiver }} ^__Ð{{ amount }}__ ^__doge__ ^__(${{ value_usd }})__ ^[[help]](" + link_help + ")  [link](https://chain.so/tx/DOGETEST/{{ txid }})")
message_withdraw = ("__^[wow ^so ^verify]__: ^/u/{{ username }} ^-> ^{{ receiver_address }} ^__Ð{{ amount }}__ ^__doge__ ^__(${{ value_usd }})__ ^[[help]](" + link_help + ")")
message_footer = ("\n\n*****" \
                 "\n\nNew to Dogecoin or " + config.bot_name + "? Ask the community any questions on /r/dogecoin!" \
                 "\n\n^quick ^commands |&nbsp;" \
                 "\n---|---" \
                 "\n^Past ^tips|^[+history](" + link_history + ")" \
                 "\n^Get ^account ^details|^[+info](" + link_info + ")" \
                 "\n^Balance|^[+balance](" + link_balance + ")" \
                 "\n^Help ^me!|^[+help](" + link_help + ")" \
                 "\n\n__PROTIP:__ An example tip would be: +/u/" + config.bot_name + " 100 doge")

# GARYLITTLEMORE OR SOMEONE ELSE PLS PUT A HELPFUL MESSAGE IN message_help BELOW FOR +help COMMAND
# (put a placeholder for anything like Dogecoin addresses for me to properly code in) :)
message_help = ("First of all, Welcome to Doge and the DogeTipBot!\n\nThe community is extremely important to us, and we\'re always happy to see new faces and help them get excited about the most fun and social coin out there.\n\nTo learn more about Doge in general, you might want to check out /r/dogecoin, where I\'m sure you\'ll find someone willing to talk your ears off about the coin.\n\nUnlike most tipping services, the DogeTipBot is \"on chain\" and transparent. What this means is that we gave up the ability to send tips super quickly in exchange for your money being verifiably yours.\n\nThis is your wallet ID: {{ address }}\n\nYou can verify the funds are actually deposited by clicking on that link, which shows your balance using block chain explorer.\n\nHow to use the DogeTipBot:\n\nTo tip someone:\n\nReply to their Reddit comment, or Reddit post with: +" + config.bot_name + " [number of doges] doge\n\nFor example:\n\n +" + config.bot_name + " 100 doge\n\nWill tip the poster you are commenting on with 100 Dogecoins. Wow!")

message_recipient_register = ("__^[such ^error]__: ^/u/{{ username }} ^needs ^to ^[register](" + link_register + ") ^before ^receiving ^any ^tips. __^\(this ^tip ^has ^been ^saved ^for ^3 ^days)__ ^[[help]](" + link_help + ")")
message_recipient_need_register_title = ("Someone sent you a Dogecoin tip of Ð{{ amount }}, and you need to register to receive it!")
message_recipient_need_register_message =  ("Hello /u/{{ username }}! You need to register an account before you can receive __{{ sender }}\'s__ Dogecoin tip of __Ð{{ amount }} doge (${{ value_usd }})__." \
                        "\n\nTo register an account:" \
                        "\n\n1. [Click here](" + link_register + ") to send a pre-filled +register message" \
                        "\n\n2. Click the \"Send\" button" \
                        "\n\n3. Receive the successful register message" \
                        "\n\nThe successful register message will contain your Dogecoin address to your tipping account.")
