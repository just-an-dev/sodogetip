#!/usr/bin/env python
#  -*- coding: utf-8 -*-
from jinja2 import Template

link_register = "https://www.reddit.com/message/compose?to=sodogetiptest&subject=\%2Bregister&message=\%2Bregister"
link_help = "https://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Bhelp&message=%2Bhelp"
link_withdraw = "https://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Bwithdraw&message=%2Bwithdraw%20AMOUNT%20doge%20to%20ADDRESS"
link_history = "https://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Bhistory&message=%2Bhistory"
link_info = "https://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Binfo&message=%2Binfo"
link_balance = "https://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Bbalance&message=%2Bbalance"

message_register_success = "Hello %s ! Your account is now registered and ready to tip Dogecoins :)" \
                           "\n\nYour wallet address is: %s" \
                           "\n\nWondering how to get tipped Dogecoins? Participate in /r/dogecoin!" \
                           "\n\nIf you need help using me (such as tipping people), you can send me a +help message [here](" + link_help + ") to receive a getting started guide." \
                           "\n\n**DID YOU KNOW?:** Unlike other tip bots, this one is non-profit and maintained by the community. Checkmate!"

message_need_register = Template("Hello {{ username }} ! You need to register an account before you can use me." \
                        "\n\nTo register an account:" \
                        "\n\n1. [Click here](" + link_register + ") to send a pre-filled +register message" \
                        "\n\n2. Click the \"Send\" button" \
                        "\n\n3. Receive the successful register message" \
                        "\n\nThe successful register message will contain your Dogecoin address to your tipping account.")

message_invalid_amount = "**^[such ^error]**: ^The ^tip ^amount ^must ^be ^at ^least ^1 ^doge. ^[[help]](" + link_help + ")"
message_balance_low_tip = "**^[such ^error]**: ^/u/%s\"s ^balance ^is ^too ^low ^for ^this ^tip ^[[help]](" + link_help + ")"
message_already_registered = "You are already registered!"
message_balance_low_withdraw = "Hello %s! It seems your balance of **Ð%s** is too low for this withdraw amount of **Ð%s**." \
                               "\n\n[Want to try again?](" + link_withdraw + ")"

message_account_details = "\n\nHere are your account details %s !" \
                          "\n\n^very ^info | &nbsp;" \
                          "\n---|---" \
                          "\n^Your ^balance | %s doge" \
                          "\n^Deposit ^address | %s " \
                          "\n^Withdraw | ^[+withdraw](" + link_withdraw + ")"
message_not_supported = "**^[such ^error]**: ^That ^is ^currently ^not ^supported! ^[[help]](" + link_help + ")"
message_balance = "Hello %s! Your balance is: %s ($%s)"
message_history = "Hello %s! Here is your transaction history: \n\n"
message_tip = "**^[wow ^so ^verify]**: ^/u/%s ^-> ^/u/%s ^**Ð%s** ^**doge (%s)** ^[[help]](" + link_help + ")"
message_withdraw = "**^[wow ^so ^verify]**: ^/u/%s ^-> ^%s ^**Ð%s** ^**doge (%s)** ^[[help]](" + link_help + ")"
message_footer = "\n\n*****" \
                 "\n\nNew to Dogecoin or sodogetip? Ask the community any questions on /r/dogecoin!" \
                 "\n\n^quick ^commands |&nbsp;" \
                 "\n---|---" \
                 "\n^Past ^tips|^[+history](" + link_history + ")" \
                 "\n^Get ^account ^details|^[+info](" + link_info + ")" \
                 "\n^Balance|^[+balance](" + link_balance + ")" \
                 "\n^Help ^me!|^[+help](" + link_help + ")" \
                 "\n\n**PROTIP:** An example tip would be: +/u/sodogetiptest 100 doge"

# GARYLITTLEMORE OR SOMEONE ELSE PLS PUT A HELPFUL MESSAGE IN message_help BELOW FOR +help COMMAND
# (put a placeholder for anything like Dogecoin addresses for me to properly code in) :)
message_help = "To tip someone: \n\n Reply to their comment or post with: +/u/sodogetipbot 100 doge" \
               "\n\nReplace 100 with whatever amount you want to tip" \
               "\n\n*****"

message_recipient_register = "**^[such ^error]**: ^/u/%s ^needs ^to ^[register](" + link_register + ") ^before ^receiving ^any ^tips ^(this ^tip ^has ^been ^saved ^for ^3 ^days) ^[[help]](" + link_help + ")"
message_recipient_need_register_title = "Someone sent you a Dogecoin tip of Ð%s, and you need to register to receive it!"
message_recipient_need_register_message = "Hello %s! You need to register an account before you can receive **%s\"s** Dogecoin tip of **Ð%s doge ($%s)**." \
                        "\n\nTo register an account:" \
                        "\n\n1. [Click here](" + link_register + ") to send a pre-filled +register message" \
                        "\n\n2. Click the \"Send\" button" \
                        "\n\n3. Receive the successful register message" \
                        "\n\nThe successful register message will contain your Dogecoin address to your tipping account."