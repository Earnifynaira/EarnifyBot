import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Telegram Bot Token
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL Database URL
FLUTTERWAVE_PAYMENT_URL = os.getenv("FLUTTERWAVE_PAYMENT_URL")  # Flutterwave Payment Link
FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")  # Flutterwave Secret Key
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Telegram User ID for Admin Controls

