import telebot
import time
import schedule
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import connect_db
from config import TOKEN, FLUTTERWAVE_PAYMENT_LINK

bot = telebot.TeleBot(TOKEN)

# 📌 Register User
def register_user(user_id, username, referred_by=None):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.execute("INSERT INTO users (user_id, username, referred_by) VALUES (%s, %s, %s)",
                    (user_id, username, referred_by))
        conn.commit()
    cur.close()
    conn.close()

# 📌 Get User Info
def get_user(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# 📌 Update User Balance
def update_balance(user_id, amount):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    cur.close()
    conn.close()

# 📌 Handle `/start` Command (Referral System)
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.chat.username or "NoUsername"

    referred_by = None
    if len(message.text.split()) > 1:
        referred_by = int(message.text.split()[1])

    register_user(user_id, username, referred_by)

    bot.send_message(user_id, f"👋 Welcome to EarnifyBot!\n\nEarn money by clicking and referring friends!\n\nYour referral link:\nhttps://t.me/Earnifynairabot?start={user_id}")

# 📌 Handle "Click to Earn"
@bot.message_handler(func=lambda message: message.text == "💰 Click to Earn")
def click_to_earn(message):
    user_id = message.chat.id
    user = get_user(user_id)

    if not user:
        bot.send_message(user_id, "❌ You are not registered. Use /start to begin.")
        return

    update_balance(user_id, 10000)
    bot.send_message(user_id, "✅ You've earned ₦10,000! Come back in 15 minutes.")

# 📌 Handle "Withdraw"
@bot.message_handler(func=lambda message: message.text == "💵 Request Withdrawal")
def withdraw_request(message):
    user_id = message.chat.id
    user = get_user(user_id)

    if not user:
        bot.send_message(user_id, "❌ You are not registered. Use /start to begin.")
        return

    if user[3] < 100000:
        bot.send_message(user_id, "❌ Minimum withdrawal amount is ₦100,000.")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Pay ₦1,500 for Verification", url=FLUTTERWAVE_PAYMENT_LINK))

    bot.send_message(user_id, "💳 Before withdrawing, verify your account by paying ₦1,500. ₦1,000 will be refunded after verification.", reply_markup=markup)

# 📌 Handle Admin Approvals
@bot.message_handler(commands=['approve'])
def approve_withdrawal(message):
    if message.chat.id != ADMIN_ID:
        return
    
    try:
        withdraw_id = int(message.text.split()[1])
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE withdrawals SET status = 'approved' WHERE id = %s", (withdraw_id,))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(ADMIN_ID, f"✅ Withdrawal ID {withdraw_id} approved.")
    except:
        bot.send_message(ADMIN_ID, "❌ Invalid command format. Use: /approve <withdraw_id>")

# 📌 Hourly Broadcast
def send_hourly_broadcast():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    for user in users:
        bot.send_message(user[0], "⏳ Reminder: You can now claim your ₦40,000 for this hour! Click '💰 Click to Earn' now.")

schedule.every().hour.at(":01").do(send_hourly_broadcast)

# 📌 Start Bot & Scheduler
def run_bot():
    while True:
        schedule.run_pending()
        time.sleep(1)

import threading
threading.Thread(target=run_bot).start()
bot.polling()
