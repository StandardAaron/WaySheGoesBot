#!/usr/bin/python
import os, sys, time
import telebot
import datetime
import logging
import operator
import numpy

'''Grab your bot token from a textfile (.token). This is required to run.'''
try:
    with open('.token', 'r') as token_file:
        TOKEN = token_file.readline().strip()
except Exception as e:
    sys.exit(e)

#init the bot
bot = telebot.TeleBot(TOKEN)

master_items = [u'\U0001F352',
                u'\U00002666',
                u'\U0001F4A9',
                u'\U00002764',
                u'\U0001F36B',
                u'\U0001F34B',
                u'\U0001F4B0',
                u'\U0001F6AC',
                u'\U00000037\U0000FE0F\U000020E3']

'''
commands=[] is the list of supported commands to which the bot with reply.
current behaviour of this bot is to ignore any commands or messages that 
are not in the approved command list.
'''
@bot.message_handler(commands=['slots', 'vlts', 'vlt'])
def send_message(message):
    print(message)
    reply = slot_handler(message)
    print(reply)
    bot.reply_to(message, reply)

def slot_handler(message):
    # set today's date and check if it aligns with the tracker
    today = datetime.date.today().strftime('%Y%m%d')
    if not today == credit_tracker.current_date:
        credit_tracker.reset()
    user_id = message.from_user.id #the Telegram UID

    # check for the user in the credit_tracker, if found, set
    # remaining credit, else add them and give them some smokes.
    try:
        remaining_credits = credit_tracker.user_credit_map[user_id]
        if remaining_credits < 1:
            return "Sorry there, Rick, but you got no more cans of ravioli\n Way she goes."
    except:
        print("user {0} not found in map, adding with 5 credits.".format(user_id))
        credit_tracker.add_user(user_id, 5)
        remaining_credits = 5
    
    # determine bet size based on int passed after /command.
    # if this is > total credits, bet them all.
    try:
        bet = int(message.text.split(' ')[1])
        print(bet)
        if bet < 1:
            bet = 1
    except:
        bet = 1
    if bet > remaining_credits:
        bet = remaining_credits

    # Take 4 items out of the master_items list at random to play with.
    # This helps keep the graphics rotating and fresh without making 
    # the odds of winning nearly impossible.
    numpy.random.shuffle(master_items)
    slot_items = master_items[:4]
    print(slot_items)

    # This is the actual slot-pull result represented in a 
    # 2-dimensional (3x3) numpy array generated from randomly chosing
    # index values from slot_items (which, remember, is randomly paired-down
    # version of master_items). This allows Ray to do the row/col/diag
    # comparisions in pure interger math, and then we look-up the 
    # unicode values to send in the reply message on Telegram
    slot_array = numpy.random.choice(len(slot_items), (3,3))
    print(slot_array)
    win_lines = 0 # set the number of winning lines for this pull.
    line_list = deconstruct_array(slot_array)
    for l in line_list:
        if len(set(l)) == 1:
            win_lines += 1
    total_score = bet * win_lines #extra-line multiplier
    if total_score == 0:
        total_score = -bet # ding this user for their total bet amount
    credit_tracker.credit_change(user_id, total_score)
    fullname = str(message.from_user.first_name + ' ' + message.from_user.last_name)
    return_text = """{0} pulled the one arm bandit and got:\n
                     {1}    {2}      {3}\n
                     {4}    {5}      {6}\n
                     {7}    {8}      {9}\n
                    """.format(fullname,
                                *[slot_items[i] for i in numpy.nditer(slot_array)])
    if win_lines > 0:
        return_text += '''You won on {0} line(s).\n
                     That's {1} more cans of ravioli for you, there, Rick.\n
                     You now have a total of {2} credits!
                     '''.format(win_lines,
                                total_score,
                                credit_tracker.user_credit_map[user_id])
    else:
        return_text += '''Way to go Cory and Trevor, you lost {0} credits,\n
                        Now you only have {1} left.\n 
                        Smokes, let's go!'''.format(total_score,credit_tracker.user_credit_map[user_id])
    return return_text

def deconstruct_array(a):
    '''
    This function lists out every 1x3 array (list) that constitutes a possible
    line in the slot result. This is done so that we can iterate over it and check
    for 3-in-a-rows.

    Parameters
    ----------
    a - 2 dimensional 3x3 numpy array

    Returns
    -------
    line_list : list of lists
    '''
    line_list = []
    line_list.append(numpy.diagonal(a))
    line_list.append(numpy.diagonal(numpy.fliplr(a)))
    for i in a:
        line_list.append(i)
    for i in numpy.rot90(a):
        line_list.append(i)
    return line_list

class userCreditTracker(object):
    def __init__(self):
        self.reset()

    def add_user(self, user_id, credits=0):
        self.user_credit_map[user_id] = credits

    def credit_change(self, user_id, credit_delta):
        self.user_credit_map[user_id] += credit_delta
    
    def reset(self):
        self.current_date = datetime.date.today().strftime('%Y%m%d')
        self.user_credit_map = {}

if __name__ == '__main__':
    #init the global tracker
    credit_tracker = userCreditTracker()
    #start the bot in polling mode
    bot.polling()