import os
import threading
import schedule
import time
import logging
import requests
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
from database import connect_db
from config import TOKEN, FLUTTERWAVE_PAYMENT_LINK, WEBHOOK_URL, ADMIN_ID  # ✅ Import ADMIN_ID from config.py

# ✅ Set Up Bot & Flask
bot = Bot(token=TOKEN)
app = Flask(__name__)

# ✅ Set Up Dispatcher
dispatcher = Dispatcher(bot, None, workers=0)

# ✅ Register User in Database
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

# ✅ Fetch User Data
def get_user(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# ✅ Update User Balance
def update_balance(user_id, amount):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    cur.close()
    conn.close()

# ✅ Handle `/start` Command (Referral System)
def start(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    username = update.message.chat.username or "NoUsername"

    referred_by = None
    if context.args:
        referred_by = int(context.args[0])

    register_user(user_id, username, referred_by)

    update.message.reply_text(
        f"👋 Welcome to EarnifyBot!\n\nEarn money by clicking and referring friends!\n\n"
        f"Your referral link:\nhttps://t.me/Earnifynairabot?start={user_id}"
    )

# ✅ Handle "Click to Earn"
def click_to_earn(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    user = get_user(user_id)

    if not user:
        update.message.reply_text("❌ You are not registered. Use /start to begin.")
        return

    update_balance(user_id, 10000)
    update.message.reply_text("✅ You've earned ₦10,000! Come back in 15 minutes.")

# ✅ Handle "Withdraw Request"
def withdraw_request(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    user = get_user(user_id)

    if not user:
        update.message.reply_text("❌ You are not registered. Use /start to begin.")
        return

    if user[3] < 100000:
        update.message.reply_text("❌ Minimum withdrawal amount is ₦100,000.")
        return

    markup = InlineKeyboardMarkup([[InlineKeyboardButton("Pay ₦1,500 for Verification", url=FLUTTERWAVE_PAYMENT_LINK)]])

    update.message.reply_text(
        "💳 Before withdrawing, verify your account by paying ₦1,500. ₦1,000 will be refunded after verification.",
        reply_markup=markup
    )

# ✅ Handle Admin Approval (`/approve <withdraw_id>`)
def approve_withdrawal(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    if user_id != int(ADMIN_ID):  # ✅ Check Admin Privileges
        return

    try:
        withdraw_id = int(context.args[0])
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE withdrawals SET status = 'approved' WHERE id = %s", (withdraw_id,))
        conn.commit()
        cur.close()
        conn.close()
        update.message.reply_text(f"✅ Withdrawal ID {withdraw_id} approved.")
    except:
        update.message.reply_text("❌ Invalid command format. Use: /approve <withdraw_id>")

# ✅ Hourly Broadcast Function
def broadcast_message():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    for user in users:
        bot.send_message(user[0], "⏳ Reminder: You can now claim your ₦40,000 for this hour! Click '💰 Click to Earn' now.")

# ✅ Schedule Hourly Broadcast
def schedule_broadcast():
    schedule.every().hour.at(":01").do(broadcast_message)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True
    thread.start()

# ✅ Webhook Route for Telegram Updates
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_update = request.get_json()
    if json_update:
        update = Update.de_json(json_update, bot)
        dispatcher.process_update(update)
    return "OK", 200

# ✅ Set Webhook
def set_webhook():
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

# ✅ Root Route
@app.route("/")
def home():
    return "EarnifyBot is Running!", 200

# ✅ Register Handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text("💰 Click to Earn"), click_to_earn))
dispatcher.add_handler(MessageHandler(Filters.text("💵 Request Withdrawal"), withdraw_request))
dispatcher.add_handler(CommandHandler("approve", approve_withdrawal, pass_args=True))

# ✅ Run Flask App
if __name__ == "__main__":
    set_webhook()
    schedule_broadcast()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
