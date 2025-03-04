import os 
import threading
import schedule
import time
import logging
import requests
import asyncio
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database import connect_db
from config import TOKEN, FLUTTERWAVE_PAYMENT_LINK, WEBHOOK_URL, ADMIN_ID

# ✅ Initialize Telegram Bot & Flask App
app = Flask(__name__)
bot_app = Application.builder().token(TOKEN).build()

# ✅ Register User in Database
def register_user(user_id, username, referred_by=None):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute("INSERT INTO users (user_id, username, referred_by) VALUES (%s, %s, %s)", 
                    (user_id, username, referred_by))
        conn.commit()
    cur.close()
    conn.close()

# ✅ Update User Balance
def update_balance(user_id, amount):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    cur.close()
    conn.close()

# ✅ Handle `/start` Command
async def start(update: Update, context):
    user_id = update.message.chat.id
    username = update.message.chat.username or "NoUsername"
    referred_by = int(context.args[0]) if context.args else None

    register_user(user_id, username, referred_by)

    await update.message.reply_text(
        f"👋 Welcome to EarnifyBot!\n\nEarn money by clicking and referring friends!\n\n"
        f"Your referral link:\nhttps://t.me/Earnifynairabot?start={user_id}"
    )

# ✅ Handle "Click to Earn"
async def click_to_earn(update: Update, context):
    user_id = update.message.chat.id

    update_balance(user_id, 10000)
    await update.message.reply_text("✅ You've earned ₦10,000! Come back in 15 minutes.")

# ✅ Webhook Route for Telegram Updates
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_update = request.get_json()
    if json_update:
        update = Update.de_json(json_update, bot_app.bot)
        asyncio.run_coroutine_threadsafe(bot_app.update_queue.put(update), bot_app._loop)
    return "OK", 200

# ✅ Set Webhook
async def set_webhook():
    await bot_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

# ✅ Register Handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.Text("💰 Click to Earn"), click_to_earn))

# ✅ Start Flask & Bot
if __name__ == "__main__":
    asyncio.run(bot_app.initialize())  # Automatically sets webhook
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
