#!/usr/bin/python
import datetime
import os
import sqlite3
import sys
import time

import numpy
import telebot

# Grab your bot token from a textfile (.token). This is required to run.
try:
    with open('.token', 'r') as token_file:
        TOKEN = token_file.readline().strip()
except Exception as e:
    sys.exit(e)

#init the bot
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

master_items = [u'\U0001F352',
    u'\U0001F4A9',
    u'\U0001F36B',
    u'\U0001F4B0',
    u'\U0001F6AC',
    u'\U0001F37A',
    u'\U0001F99E',
    u'\U0001F41D',
    u'\U00000037\U0000FE0F\U000020E3']

'''
commands=[] is the list of supported commands to which the bot with reply.
current behaviour of this bot is to ignore any commands or messages that 
are not in the approved command list.
'''

@bot.message_handler(commands=['slots', 
    'vlts', 
    'vlt', 
    'bank', 
    'ray'])

def send_message(message):
    split_message = message.text.split(' ')
    print(message)
    if message.text[:5] == '/bank':
        reply = bank_handler(message)
    elif message.text[:4] == '/ray':
        reply = help_handler()
    else:
        reply = slot_handler(message)
    print(reply)
    bot.reply_to(message, reply)
    
def help_handler():
    return_text = ("<pre>"
        "/ray \n"
        "------ \n"
        "This message.\n\n"

        "/bank \n"
        "----- \n"
        "return bank totals.\n\n"

        "/slots /vlt /vlts N\n"
        "------------------- \n"
        "play the slots with N credits.\n\n"

        "Today's VLT symbols\n"
        "--------------------\n")
    for i in master_items:
        return_text += i
    return_text += "</pre>"
    return return_text

def slot_handler(message):
    # set today's date and check if it aligns with the tracker
    today = datetime.date.today().strftime('%Y%m%d')
    user_id = message.from_user.id #the Telegram UID
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)
    print(type(user_name))
    print(user_name)
    # check for the user in the bank_tracker, if found, set
    # remaining credit, else add them and give them some smokes.
    try:
        user_last_accessed = bank_tracker.query_user_table(user_id)[2]
    except:
        user_last_accessed = ''
    bank_tracker.populate_user_table(user_id, user_name, today)
    try:
        current_user_bank = bank_tracker.get_user_bank(user_id)[1]
        if current_user_bank < 1:
            return ('Sorry there, Rick, but I gotta cut ya off.\n '
                'Way she goes (Maybe Julian will lend you some chips?)')
    except:
        print('user {0} not found in DB, adding with 500 chips'.format(user_id))
        bank_tracker.add_or_upd_user_credit(user_id, 500)
        current_user_bank = 500
    
    # determine bet size based on int passed after /command.
    # if this is > total credits, bet 'em all.
    try:
        bet = int(message.text.split(' ')[1])
        print(bet)
        if bet < 1:
            bet = 1
    except:
        bet = 1
    if bet > current_user_bank: # If you bet the farm...
        bet = current_user_bank # you bet the farm :D
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
        updated_user_bank = current_user_bank - bet # ding this user for their total bet amount
    else:
        updated_user_bank = current_user_bank + total_score # credit
    bank_tracker.add_or_upd_user_credit(user_id, updated_user_bank)
    return_text = (
        "<pre>"
        "{}    {}    {}\n\n"
        "{}    {}    {}\n\n"
        "{}    {}    {}\n"
        "</pre>").format(*[slot_items[i] for i in numpy.nditer(slot_array)])
    if win_lines > 0:
        return_text += ("Your bet of {0} won on {1} line(s) for a total of {2}."
                     "You now have a total of {3} credits!").format(bet, win_lines,
                                                                    total_score,
                                                                    updated_user_bank)
    else:
        return_text += "Good job CYRUS. you lost {0} credits.\n".format(bet)
        if updated_user_bank < 1:
            return_text += "You're out of credits now, why don't you go study for your Grade 10!?"
        else:
            return_text += "Now you have {0} left. Smokes, let's go!".format(updated_user_bank)
    return return_text

def bank_handler(message):
    split_message = message.text.split(" ")
    # For now, we'll let people borrow indiscriminately, but we should implement a limit,
    # an auto-payback system, etc.
    if len(split_message) > 2 and split_message[1] == 'lend':
        try:
            user_id_to_upd = bank_tracker.resolve_user_id(split_message[2])
            return_text = (
                "OK, Ill lend {0} 1000 credits, "
                "Bubbs, but only 'cause you're askin'.".format(user_id_to_upd))            
            print(user_id_to_upd)
            bank_tracker.add_or_upd_user_credit(user_id_to_upd, 1000)
        except:
            return_text = ("That's not gonna happen, "
                "you haven't been payin' into EI ... "
                "UI ... whatever you call it.")
    else:
        user_bank = bank_tracker.get_user_bank(message.from_user.id)
        return_text = "{} your balance is {}.\n".format(*user_bank)
        leader_tup = bank_tracker.get_leader()
        if leader_tup[0] == user_bank[0]:
            return_text += "You are the current bank leader."
        else:
            return_text += "Leader is {} with {} chips.\n".format(*leader_tup)
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

class bankTracker(object):
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
            self.db_conn.execute("CREATE TABLE bank "
                "(user_id INT UNIQUE, "
                "balance INT, "
                "debt INT)")
            self.db_conn.execute("CREATE TABLE users "
                "(user_id INT UNIQUE, "
                "user_name TEXT, "
                "last_accessed TEXT, "
                "last_borrowed TEXT, "
                "borrow_count INT)")
            self.db_conn.commit()
    
    def populate_user_table(self, user_id, user_name, last_accessed, last_borrowed='', borrow_count=0):
        sql = ("INSERT or REPLACE "
            "INTO users "
            "VALUES({0}, '{1}', '{2}', '{3}', {4})".format(user_id, 
                user_name,
                last_accessed,
                last_borrowed,
                borrow_count))
        print(sql)
        self.db_conn.execute(sql)
    
    def query_user_table(self, user_id):
        sql = "SELECT * FROM users WHERE user_id = {0}".format(user_id)
        cur_result = self.db_conn.execute(sql)
        return cur_result.fetchone()

    def add_or_upd_user_credit(self, user_id, transaction, debt=0):
        try:
            user_bank_details = get_user_bank(user_id)
            current_bank = user_bank_details[1] # eventually factor debt into this, but for now ¯\_(ツ)_/¯
            current_bank += transaction
        except:
            # Couldn't get the user bank info so assume it's non-existant
            current_bank = transaction
        sql = ("INSERT or REPLACE INTO bank "
            "VALUES({0}, {1}, {2})".format(user_id, current_bank, debt))
        self.db_conn.execute(sql)
        self.db_conn.commit()
    
    def get_user_bank(self, user_id):
        sql = ("SELECT u.user_name, b.balance "
            "FROM users u, bank b "
            "WHERE u.user_id == b.user_id "
            "AND u.user_id = {0}").format(user_id)
        cursor_result = self.db_conn.execute(sql)
        return cursor_result.fetchone()

    def get_leader(self):
        sql = ("SELECT u.user_name, b.balance "
            "FROM users u, bank b "
            "WHERE b.balance == (SELECT max(balance) from bank) "
            "AND b.user_id == u.user_id")
        cur_result = self.db_conn.execute(sql)
        return cur_result.fetchone()

    def resolve_user_id(self, user_string):
        sql = ("SELECT user_id FROM users "
            "WHERE upper(user_name) like '%{0}%'").format(user_string.upper())
        print(sql)
        cur_result = self.db_conn.execute(sql)
        return cur_result.fetchone()[0]

if __name__ == '__main__':
    #init the global tracker
    db_file = 'bank_tracker.sqlite3db'
    bank_tracker = bankTracker(db_file)
    #start the bot in polling mode
    bot.polling(none_stop=True, timeout=90)
