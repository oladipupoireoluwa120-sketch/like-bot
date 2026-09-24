import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

@app.route('/')
def home():
    return "LikeBot is alive! 🔥"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 LikeBot is LIVE! Send /start to use LikeBooster.")

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("🔥 LikeBot starting...")
    application.run_polling()

if __name__ == "__main__":
    # Start bot in background thread
    threading.Thread(target=run_bot, daemon=True).start()
    # Start web server for Render
    app.run(host="0.0.0.0", port=PORT)