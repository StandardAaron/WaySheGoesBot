#!/usr/bin/python
import os, sys, time
import telebot
import datetime
import numpy
import sqlite3

"""
TO-DO:
1) refactor duplicate actions (like moving credits into bank, which we do twice)
2) create a better "message" object to pass around that has all the variables
    we want/need already parsed instead of doing it in every func.
3) fix race condition if someone transfers before issuing their first pull
    of the day, they lose the transferred creds, and get 5 in their place.
"""


'''Grab your bot token from a textfile (.token). This is required to run.'''
try:
    with open('.token', 'r') as token_file:
        TOKEN = token_file.readline().strip()
except Exception as e:
    sys.exit(e)

#init the bot
bot = telebot.TeleBot(TOKEN)

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
@bot.message_handler(commands=['slots', 'vlts', 'vlt', 'bank', 'ray'])
def send_message(message):
    split_message = message.text.split(' ')
    print(message)
    if message.text[:5] == '/bank':
        reply = bank_handler(message)
    elif message.text[:2] == '/r' and split_message[0][-2:] == 'ay':
        reply = help_handler(message)
    else:
        reply = slot_handler(message)
    print(reply)
    bot.reply_to(message, reply)

def help_handler(message):
    split_message = message.text.split(" ")
    if message.from_user.id == 942327020 and len(split_message) > 2 and split_message[1] == 'lend':
        try:
            return_text = "OK, Ill lend {0} 1000 credits, Bubbs, but only 'cause you're askin'.".format(split_message[2])
            user_id_to_upd = credit_tracker.resolve_user_id(split_message[2])
            print(user_id_to_upd)
            credit_tracker.add_or_upd_user_credit(user_id_to_upd, credits=1000)
        except:
            return_text = "That's not gonna happen, you haven't been payin' into EI ... UI ... whatever the fuck you call it"
    else:
        return_text = ('/ray: This message.\n'
                '/bank: return bank totals.\n'
                '/bank wd 00: withdraw 00 credits from your bank.\n'
                '/bank dep: immediately deposit all your daily credits into your bank.\n'
                '/slots - /vlt - /vlts 00 - play the slots with 00 credits.\n'
                'Happy 24(00) credits day!'
                "Today's VLT symbols are:\n")
        for i in master_items:
            return_text += i
    return return_text

def slot_handler(message):
    # set today's date and check if it aligns with the tracker
    today = datetime.date.today().strftime('%Y%m%d')
    user_id = message.from_user.id #the Telegram UID
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)
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
        credit_tracker.add_or_upd_user_credit(user_id, 5, 0)
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
    return_text = (" {}    {}      {}\n\n"
                     "{}    {}      {}\n\n"
                     "{}    {}      {}\n").format(*[slot_items[i] for i in numpy.nditer(slot_array)])
    if win_lines > 0:
        return_text += ("Your bet of {0} won on {1} line(s) for a total of {2}."
                     "You now have a total of {3} credits!").format(bet, win_lines,
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
    actions = ['wd', 'dep']
    try:
        bank_action = message.text.split(' ')[1]
    except:
        bank_action = 'None'
    if bank_action not in actions:
        return_text = bank_statement()
    elif bank_action == 'wd':
        return_text = bank_withdraw(message)
    elif bank_action == 'dep':
        return_text = bank_deposit(message)
    return return_text

def bank_withdraw(message):
    user_id = message.from_user.id
    try:
        user_current_stats = credit_tracker.get_user_credit(user_id)
        user_current_bank = user_current_stats[2]
        user_current_credit = user_current_stats[1]
    except:
        return 'Cant load your bank right now.'
    try:
        wd_amount = int(message.text.split(' ')[2])
    except:
        return 'Unknown amount for withdrawal.'
    if user_current_bank >= wd_amount:
        user_current_bank -= wd_amount
        user_current_credit += wd_amount
        credit_tracker.add_or_upd_user_credit(user_id,
                                            user_current_credit,
                                            user_current_bank)
    return 'Transfer of {} credits complete.'.format(wd_amount)

def bank_deposit(message):
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)
    try:
        credit_info = credit_tracker.get_user_credit(user_id)
        new_bank = int(credit_info[1] + credit_info[2])
        credit_tracker.add_or_upd_user_credit(user_id, 0, new_bank)
    except:
        pass
    return_text = "Moved {0}'s {1} credits into the bank".format(user_name, credit_info[1])
    return return_text

def bank_statement():
    sql = ("SELECT u.user_name, c.credits, c.bank "
        "FROM users u, credit_tracker c "
        "WHERE u.user_id == c.user_id ")
    cur_result = credit_tracker.db_conn.execute(sql)
    return_text = 'USER                CREDITS     BANK\n'
    for i in cur_result.fetchall():
        return_text += "{}:    {}     {}\n".format(*i)
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

    def add_or_upd_user_credit(self, user_id, credits=0, bank=0):
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

    def resolve_user_id(self, user_string):
        sql = ("SELECT user_id FROM users "
                "WHERE upper(user_name) like '%{0}%'").format(user_string.upper())
        print(sql)
        cur_result = self.db_conn.execute(sql)
        return cur_result.fetchone()[0]

if __name__ == '__main__':
    #init the global tracker
    db_file = 'credit_tracker.sqlite3db'
    credit_tracker = userCreditTracker(db_file)
    #start the bot in polling mode
    bot.polling(none_stop=True, timeout=90)
