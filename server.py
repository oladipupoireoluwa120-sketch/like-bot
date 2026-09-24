from flask import Flask
import threading, os
import bot

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "LikeBot LIVE!"

def run_bot():
    bot.main()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)