from flask import Flask
import threading
import bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running! ✅"

def run_bot():
    bot.main()

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
