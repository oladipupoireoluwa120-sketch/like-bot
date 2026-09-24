import sqlite3, warnings, re, asyncio, os, random, string, threading
warnings.filterwarnings("ignore")
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler, ChatMemberHandler
from telegram.request import HTTPXRequest
from telegram.constants import ChatMemberStatus

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Set BOT_TOKEN env var on Render!")

ADMIN_ID = 8805633124
ACCOUNT_NUMBER = "6143597127"
ACCOUNT_NAME = "IREOLUWA SAMUEL OLADIPUPO"
FORCE_CHANNEL_ID = -1004432894885
PROOF_CHANNEL_ID = -1003887562036

PACKAGES = {
    "1000": {"likes": 1000, "price": 100},
    "3000": {"likes": 3000, "price": 250},
    "5000": {"likes": 5000, "price": 400},
    "10000": {"likes": 10000, "price": 700},
    "upsell_2000": {"likes": 2000, "price": 150}
}

UID, NAME, EMAIL, PAYMENT_CHOICE, AMOUNT, RECEIPT = range(6)

db = sqlite3.connect("orders.db", check_same_thread=False)
db.execute("""CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, username TEXT, referrer_id INTEGER, referrals_count INTEGER DEFAULT 0, balance INTEGER DEFAULT 0, total_earned INTEGER DEFAULT 0, joined TEXT, banned INTEGER DEFAULT 0, fake_attempts INTEGER DEFAULT 0)""")
db.execute("""CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, txn_id TEXT, user_id INTEGER, username TEXT, ff_uid TEXT, ff_name TEXT, email TEXT, package TEXT, likes INTEGER, amount INTEGER, pay_method TEXT, status TEXT, date TEXT)""")
db.execute("""CREATE TABLE IF NOT EXISTS referrals(id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER, referred_id INTEGER, date TEXT)""")
db.execute("""CREATE TABLE IF NOT EXISTS carts(user_id INTEGER PRIMARY KEY, pkg TEXT, price INTEGER, created TEXT)""")
db.commit()

def gen_txn(): return f"LB-{''.join(random.choices(string.digits, k=5))}{random.choice(string.ascii_uppercase)}"
def main_menu(): return ReplyKeyboardMarkup([["🚀 BOOST LIKES", "💰 PACKAGES"],["👥 REFER & EARN 20%", "💳 MY BALANCE - REFER & EARN"],["📋 MY ORDERS", "🏆 TOP REFERRERS"],["ℹ️ HOW IT WORKS", "💬 SUPPORT"]], resize_keyboard=True, is_persistent=True)
async def check_joined(user_id, bot):
    try: m1 = await bot.get_chat_member(FORCE_CHANNEL_ID, user_id); ok1 = m1.status in ['member','administrator','creator']
    except: ok1 = False
    try: m2 = await bot.get_chat_member(PROOF_CHANNEL_ID, user_id); ok2 = m2.status in ['member','administrator','creator']
    except: ok2 = False
    return (ok1 and ok2), ok1, ok2
def ensure_user(u):
    if not db.execute("SELECT user_id FROM users WHERE user_id=?", (u.id,)).fetchone():
        db.execute("INSERT INTO users(user_id, username, joined) VALUES(?,?,?)", (u.id, u.username, datetime.now().strftime("%d-%m-%Y"))); db.commit()
    banned = db.execute("SELECT banned FROM users WHERE user_id=?", (u.id,)).fetchone()
    return banned and banned[0]==1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined_both, ok1, ok2 = await check_joined(update.effective_user.id, context.bot)
    if not joined_both:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{'✅' if ok1 else '❌'} JOIN OFFICIAL", url="https://t.me/likebotofficial")],[InlineKeyboardButton(f"{'✅' if ok2 else '❌'} JOIN BACKUP", url="https://t.me/likebotbackup")],[InlineKeyboardButton("✅ I Joined - Verify", callback_data="check_join")]])
        await update.message.reply_text("⚠️ JOIN BOTH CHANNELS!", reply_markup=kb); return
    if ensure_user(update.effective_user): await update.message.reply_text("🚫 Banned"); return
    await update.message.reply_text("🔥 LIKEBOT LIVE ✅", reply_markup=main_menu())

async def check_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    joined_both, _, _ = await check_joined(update.effective_user.id, context.bot)
    if joined_both: await start(update, context)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined_both, _, _ = await check_joined(update.effective_user.id, context.bot)
    if not joined_both: await update.callback_query.answer("Join both!", show_alert=True); return
    txt = update.message.text
    if txt in ["🚀 BOOST LIKES", "💰 PACKAGES"]:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 1000 - ₦100", callback_data="pkg_1000")],[InlineKeyboardButton("⭐ 3000 - ₦250 BEST", callback_data="pkg_3000")],[InlineKeyboardButton("💎 5000 - ₦400", callback_data="pkg_5000")],[InlineKeyboardButton("👑 10000 - ₦700", callback_data="pkg_10000")]])
        await update.message.reply_text("💰 SELECT PACKAGE", reply_markup=kb)

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    pkg_id = update.callback_query.data.replace("pkg_","")
    pkg = PACKAGES[pkg_id]; context.user_data["pkg"]=pkg_id; context.user_data["likes"]=pkg["likes"]; context.user_data["price"]=pkg["price"]
    context.user_data["txn"]=gen_txn()
    await update.callback_query.message.reply_text(f"✅ {pkg['likes']} Likes selected\nSend UID (11 digits):")
    return UID

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit() or len(update.message.text)!=11: await update.message.reply_text("❌ 11 digits!"); return UID
    context.user_data["uid"]=update.message.text; await update.message.reply_text("👤 Send FF Name:"); return NAME
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"]=update.message.text; await update.message.reply_text("📧 Send Email:"); return EMAIL
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "@" not in update.message.text: await update.message.reply_text("❌ Invalid email"); return EMAIL
    context.user_data["email"]=update.message.text
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"🏦 OPay - ₦{context.user_data['price']}", callback_data="pay_opay")]])
    await update.message.reply_text(f"Pay ₦{context.user_data['price']} to {ACCOUNT_NUMBER}", reply_markup=kb); return PAYMENT_CHOICE
async def payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer(); await update.callback_query.message.reply_text(f"Type {context.user_data['price']} after paying:"); return AMOUNT
async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(context.user_data["price"]) not in update.message.text: await update.message.reply_text(f"Type {context.user_data['price']} EXACT"); return AMOUNT
    await update.message.reply_text("📸 Upload receipt:"); return RECEIPT
async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txn=context.user_data["txn"]; db.execute("INSERT INTO orders(txn_id, user_id, username, ff_uid, ff_name, email, package, likes, amount, pay_method, status, date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(txn, update.effective_user.id, update.effective_user.username, context.user_data["uid"], context.user_data["name"], context.user_data["email"], context.user_data["pkg"], context.user_data["likes"], context.user_data["price"], "OPAY", "PENDING", datetime.now().strftime("%d-%m")) ); db.commit()
    await update.message.reply_text(f"📦 Order {txn} received! Pending approval", reply_markup=main_menu())
    return ConversationHandler.END
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("Cancelled", reply_markup=main_menu()); return ConversationHandler.END

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Alive"
def run_flask(): flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def build_application():
    req = HTTPXRequest(connect_timeout=30, read_timeout=30)
    app = Application.builder().token(BOT_TOKEN).request(req).build()
    conv = ConversationHandler(entry_points=[CallbackQueryHandler(select_package, pattern="^pkg_")], states={UID:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_uid)], NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)], EMAIL:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)], PAYMENT_CHOICE:[CallbackQueryHandler(payment_choice, pattern="^pay_")], AMOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)], RECEIPT:[MessageHandler(filters.PHOTO, get_receipt)]}, fallbacks=[CommandHandler("cancel", cancel)])
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join_cb, pattern="check_join"))
    app.add_handler(MessageHandler(filters.Regex("^(🚀 BOOST LIKES|💰 PACKAGES)"), menu_handler))
    app.add_handler(conv)
    return app

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    build_application().run_polling()

if __name__ == "__main__":
    main()