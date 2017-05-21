#!/usr/bin/env python
#  -*- coding: utf-8 -*-
link_register = '[register](http://www.reddit.com/message/compose?to=sodogetiptest&subject=%2Bregister&message=%2Bregister)'


message_register_success = "Hello %s! Your account is now registered and ready to tip Dogecoins :)" \
                           "\n\nYour wallet address is: %s" \
                           "\n\nWondering how to get tipped Dogecoins? Participate in /r/dogecoin!" \
                           "\n\nIf you need help using me (such as tipping people), you can send me a +help message [here](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+help&message=+help) to receive a getting started guide." \
                           "\n\n**DID YOU KNOW?:** Unlike other tip bots, this one is non-profit and maintained by the community. Checkmate!"
message_need_register = 'Hello %s! You need to register an account before you can use me.' \
                        '\n\nTo register an account:' \
                        '\n\n1. [Click here](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+register&message=+register) to send a pre-filled +register message' \
                        '\n\n2. Click the "Send" button' \
                        '\n\n3. Receive the successful register message' \
                        '\n\nThe successful register message will contain your Dogecoin address to your tipping account.'
message_invalid_amount = '**^[such ^error]**: ^The ^tip ^amount ^must ^be ^at ^least ^1 ^doge. ^[[help]](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+help&message=+help)'
message_balance_low_tip = '**^[such ^error]**: ^/u/%s ^-> ^/u/%s\'s ^balance ^is ^too ^low ^for ^this ^tip ^[[help]](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+help&message=+help)'
message_already_registered = 'You are already registered! Here are your account details:'
message_balance_low_withdraw = 'Hello %s! It seems your balance of **Ð%s** is too low for this withdraw amount of **Ð%s**.' \
                               '\n\n[Want to try again?](https://www.reddit.com/message/compose?to=sodogetiptest&subject=+withdraw&message=+withdraw%20AMOUNT%20doge%20to%20ADDRESS)'
message_info_introduction = '\n\nHere are your account details %s!'
message_account_details = '\n\n^very ^info | &nbsp;' \
                          '\n---|---' \
                          '\n^Your ^Balance | %s doge' \
                          '\n^Deposit ^Address | %s' \
                          '\n^Withdraw | ^[+withdraw](https://www.reddit.com/message/compose?to=sodogetiptest&subject=+withdraw&message=+withdraw AMOUNT doge to ADDRESS)'
message_not_supported = '**^[such ^error]**: ^That ^is ^currently ^not ^supported! ^[[help]](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+help&message=+help)'
message_balance = 'Hello %s! Your balance is: %s ($%s)'
message_history = 'Hello %s! Here is your transaction history: \n\n'
message_tip = '**^[wow ^so ^verify]**: ^/u/%s ^-> ^/u/%s ^**Ð%s** ^**doge (%s)** ^[[help]](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+help&message=+help)'
message_withdraw = 'Withdraw : %s to %s'
message_footer = '\n\n*****' \
                 '\n\nNew to Dogecoin or sodogetip? Ask the community any questions on /r/dogecoin!' \
                 '\n\n^quick ^commands |&nbsp;' \
                 '\n---|---' \
                 '\n^Past ^tips|^[+history](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+history&message=+history)' \
                 '\n^Get ^Dogecoin ^address|^[+address](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+address&message=+address)' \
                 '\n^Balance|^[+balance](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+balance&message=+balance)' \
                 '\n^Help ^Me!|^[+help](http://www.reddit.com/message/compose?to=sodogetiptest&subject=+help&message=+help)' \
                 '\n\n**PROTIP:** An example tip would be: +/u/sodogetiptest 100 doge'
# GARYLITTLEMORE OR SOMEONE ELSE PLS PUT A HELPFUL MESSAGE IN message_help BELOW FOR +help COMMAND
# (put a placeholder for anything like Dogecoin addresses for me to properly code in) :)
message_help = 'To tip someone: Reply to their comment or post with: +/u/sodogetipbot 100 doge' \
               '\n\nReplace 100 with whatever amount you want to tip' \
               '\n\n*****'
