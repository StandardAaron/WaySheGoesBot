#!/usr/bin/python
import os, sys, time
import telebot
import datetime
#import logging
#import operator
import numpy
import sqlite3

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
@bot.message_handler(commands=['slots', 'vlts', 'vlt', 'bank'])
def send_message(message):
    print(message)
    if message.text[:5] == '/bank':
        reply = bank_handler(message)
    else:
        reply = slot_handler(message)
    print(reply)
    bot.reply_to(message, reply)

def slot_handler(message):
    # set today's date and check if it aligns with the tracker
    today = datetime.date.today().strftime('%Y%m%d')
    user_id = message.from_user.id #the Telegram UID
    user_name = str(message.from_user.first_name + ' ' + message.from_user.last_name)
    print(type(user_name))
    print(user_name)
    # check for the user in the credit_tracker, if found, set
    # remaining credit, else add them and give them some smokes.
    try:
        user_last_accessed = credit_tracker.query_user_map(user_id)[2]
    except:
        user_last_accessed = ''
    if user_last_accessed != today:
        print('new day for {0}, banking/reseting...'.format(user_name))
        try:
            credit_info = credit_tracker.get_user_credit(user_id)
            new_bank = int(credit_info[1] + credit_info[2])
            credit_tracker.add_or_upd_user_credit(user_id, 5, new_bank)
        except:
            pass
    credit_tracker.populate_user_map(user_id, user_name, today)

    try:
        current_user_credits = credit_tracker.get_user_credit(user_id)[1]
        current_user_bank = credit_tracker.get_user_credit(user_id)[2]
        if current_user_credits < 1:
            return 'Sorry there, Rick, but I gotta cut ya off.\n Way she goes.'
    except:
        print('user {0} not found in map, adding with 5 credits, and an empty bank'.format(user_id))
        credit_tracker. add_or_upd_user_credit(user_id, 5, 0)
        current_user_credits = 5
        current_user_bank = 0
    
    # determine bet size based on int passed after /command.
    # if this is > total credits, bet 'em all.
    try:
        bet = int(message.text.split(' ')[1])
        print(bet)
        if bet < 1:
            bet = 1
    except:
        bet = 1
    if bet > current_user_credits:
        bet = current_user_credits

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
        remaining_credits_now = current_user_credits - bet # ding this user for their total bet amount
    else:
        remaining_credits_now = current_user_credits + total_score # credit
    credit_tracker.add_or_upd_user_credit(user_id, remaining_credits_now, current_user_bank)
    return_text = ("{0} pulled the one arm bandit and got:\n"
                    " {1}    {2}      {3}\n\n"
                     "{4}    {5}      {6}\n\n"
                     "{7}    {8}      {9}\n").format(user_name, *[slot_items[i] for i in numpy.nditer(slot_array)])
    if win_lines > 0:
        return_text += ("You won on {0} line(s).\n"
                     "That's {1} more cans of ravioli for you, there, Rick.\n"
                     "You now have a total of {2} credits!").format(win_lines,
                                                                    total_score,
                                                                    remaining_credits_now)
    else:
        return_text += "Good job CYRUS, ya dick. you lost {0} credits.\n".format(bet)
        if remaining_credits_now < 1:
            return_text += "You're out of credits now, why don't you go study for your Grade 10."
        else:
            return_text += "Now you have {0} left. Smokes, let's go!".format(remaining_credits_now)
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

def bank_handler(message):
    sql = ("SELECT u.user_name, c.bank "
        "FROM users u, credit_tracker c "
        "WHERE u.user_id == c.user_id ")
    cur_result = credit_tracker.db_conn.execute(sql)
    return_text = ''    
    for i in cur_result.fetchall():
        return_text += "{0}: {1}\n".format(*i)
    return return_text
    
class userCreditTracker(object):
    def __init__(self, db_file):
        self.db_file = db_file
        self.db_conn = sqlite3.connect(self.db_file, check_same_thread=False)
        try:
            self._init_db()
        except Exception as e:
            sys.exit(e)

    def _init_db(self):
        schema = self.db_conn.execute("SELECT name "
                                    "FROM sqlite_master "
                                    "Where type = 'table'")
        if not schema.fetchall():
            self.db_conn.execute("CREATE TABLE credit_tracker "
                                "(user_id INT UNIQUE, "
                                "credits INT, bank INT)")
            self.db_conn.execute("CREATE TABLE users "
                                "(user_id INT UNIQUE, "
                                "user_name TEXT, last_accessed TEXT)")
            self.db_conn.commit()
    
    def populate_user_map(self, user_id, user_name, last_accessed):
        sql = ("INSERT or REPLACE "
              "INTO users "
              "VALUES({0}, '{1}', '{2}')".format(user_id, user_name, last_accessed))
        print(sql)
        self.db_conn.execute(sql)
    
    def query_user_map(self, user_id):
        sql = "SELECT * FROM users WHERE user_id = {0}".format(user_id)
        cur_result = self.db_conn.execute(sql)
        return cur_result.fetchone()

    def  add_or_upd_user_credit(self, user_id, credits=0, bank=0):
        sql = ("INSERT or REPLACE "
                "INTO credit_tracker "
                "VALUES({0}, {1}, {2})".format(user_id, credits, bank))
        self.db_conn.execute(sql)
        self.db_conn.commit()
    
    def get_user_credit(self, user_id):
        cursor_result = self.db_conn.execute("SELECT * "
                                            "FROM credit_tracker "
                                            "WHERE user_id = {0}".format(user_id))
        return cursor_result.fetchone()

if __name__ == '__main__':
    #init the global tracker
    db_file = 'credit_tracker.sqlite3db'    
    credit_tracker = userCreditTracker(db_file)
    #start the bot in polling mode
    bot.polling(none_stop=True, timeout=90)