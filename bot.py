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

def main_menu():
    return ReplyKeyboardMarkup([
        ["🚀 BOOST LIKES", "💰 PACKAGES"],
        ["👥 REFER & EARN 20%", "💳 MY BALANCE - REFER & EARN"],
        ["📋 MY ORDERS", "🏆 TOP REFERRERS"],
        ["ℹ️ HOW IT WORKS", "💬 SUPPORT"]
    ], resize_keyboard=True, is_persistent=True)

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
    user = update.effective_user
    joined_both, ok1, ok2 = await check_joined(user.id, context.bot)
    if not joined_both:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{'✅' if ok1 else '❌'} JOIN OFFICIAL", url="https://t.me/likebotofficial")],
            [InlineKeyboardButton(f"{'✅' if ok2 else '❌'} JOIN BACKUP", url="https://t.me/likebotbackup")],
            [InlineKeyboardButton("✅ I Joined - Verify", callback_data="check_join")]
        ])
        await update.message.reply_text("⚠️ JOIN BOTH CHANNELS TO USE BOT! 🔒", reply_markup=kb)
        return

    if ensure_user(user):
        await update.message.reply_text("🚫 Banned. DM @MARCUSSUPPORT")
        return

    # Referral logic
    if context.args and context.args[0].startswith("REF"):
        try:
            rid = int(context.args[0].replace("REF",""))
            if rid!= user.id and not db.execute("SELECT * FROM referrals WHERE referred_id=?", (user.id,)).fetchone():
                cur = db.execute("SELECT referrer_id FROM users WHERE user_id=?", (user.id,)).fetchone()
                if cur and cur[0] is None:
                    db.execute("INSERT INTO referrals(referrer_id, referred_id, date) VALUES(?,?,?)", (rid, user.id, datetime.now().strftime("%d-%m")))
                    db.execute("UPDATE users SET referrals_count=referrals_count+1 WHERE user_id=?", (rid,))
                    db.execute("UPDATE users SET referrer_id=? WHERE user_id=?", (rid, user.id))
                    db.commit()
        except: pass

    await update.message.reply_text("🔥 *LIKEBOT OFFICIAL LIVE* ✅\n✅ 150+ Delivered\n🛡️ Money-back\n👇 Tap Menu Below", reply_markup=main_menu())

async def check_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    joined_both, _, _ = await check_joined(update.effective_user.id, context.bot)
    if joined_both:
        await update.callback_query.message.delete()
        await start(update, context)
    else:
        await update.callback_query.answer("❌ Join both channels first!", show_alert=True)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    txt = update.message.text

    joined_both, _, _ = await check_joined(user_id, context.bot)
    if not joined_both:
        await update.message.reply_text("⚠️ Join both channels first! Send /start")
        return

    if txt in ["🚀 BOOST LIKES", "💰 PACKAGES"]:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 1000 Likes - ₦100", callback_data="pkg_1000")],
            [InlineKeyboardButton("⭐ 3000 Likes - ₦250 BEST", callback_data="pkg_3000")],
            [InlineKeyboardButton("💎 5000 Likes - ₦400", callback_data="pkg_5000")],
            [InlineKeyboardButton("👑 10000 Likes - ₦700 MEGA", callback_data="pkg_10000")]
        ])
        await update.message.reply_text("💰 *SELECT PACKAGE* 👇", reply_markup=kb)
        return

    if txt == "👥 REFER & EARN 20%":
        row = db.execute("SELECT referrals_count, balance, total_earned FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row:
            c, b, e = row
            botname = (await context.bot.get_me()).username
            link = f"https://t.me/{botname}?start=REF{user_id}"
            await update.message.reply_text(f"👥 *REFER & EARN 20%* 💸\n\nYour Link:\n`{link}`\n\nRefs: {c}\nBalance: ₦{b}\nEarned: ₦{e}\n\nShare link, get 20% per sale!", reply_markup=main_menu())
        return

    if txt == "💳 MY BALANCE - REFER & EARN":
        row = db.execute("SELECT balance, referrals_count, total_earned FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row:
            bal, count, earn = row
            await update.message.reply_text(f"💳 *MY BALANCE* 💰\n\nBalance: *₦{bal}*\nRefs: {count}\nTotal Earned: ₦{earn}", reply_markup=main_menu())
        return

    if txt == "📋 MY ORDERS":
        rows = db.execute("SELECT id, txn_id, likes, status, date FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,)).fetchall()
        if not rows:
            await update.message.reply_text("📋 No orders yet!", reply_markup=main_menu())
        else:
            msg = "📋 *YOUR ORDERS*\n\n"
            for oid, txn, likes, st, date in rows:
                ic = "✅" if st=="DELIVERED" else "⏳"
                msg += f"{ic} #{oid} | {txn} | {likes} Likes | {st}\n"
            await update.message.reply_text(msg, reply_markup=main_menu())
        return

    if txt == "🏆 TOP REFERRERS":
        rows = db.execute("SELECT username, referrals_count FROM users ORDER BY referrals_count DESC LIMIT 5").fetchall()
        msg = "🏆 *TOP REFERRERS*\n\n"
        for i, (uname, cnt) in enumerate(rows, 1):
            msg += f"{i}. @{uname or 'user'} - {cnt} refs\n"
        await update.message.reply_text(msg, reply_markup=main_menu())
        return

    if txt in ["ℹ️ HOW IT WORKS", "💬 SUPPORT"]:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 DM @MARCUSSUPPORT", url="https://t.me/MARCUSSUPPORT")]])
        await update.message.reply_text(f"ℹ️ *HOW IT WORKS*\n1. Choose package\n2. Pay to OPay {ACCOUNT_NUMBER}\n3. Upload receipt\n\n💬 Support: @MARCUSSUPPORT", reply_markup=kb)
        return

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    pkg_id = update.callback_query.data.replace("pkg_","")
    pkg = PACKAGES[pkg_id]
    context.user_data["pkg"] = pkg_id
    context.user_data["likes"] = pkg["likes"]
    context.user_data["price"] = pkg["price"]
    context.user_data["txn"] = gen_txn()
    await update.callback_query.message.reply_text(f"✅ *{pkg['likes']} Likes - ₦{pkg['price']}* Selected!\n🆔 TXN: `{context.user_data['txn']}`\n\n🎮 Step 1/4: Send Free Fire UID (11 digits)")
    return UID

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_text = update.message.text.strip()
    if not uid_text.isdigit() or len(uid_text)!= 11:
        await update.message.reply_text("❌ Invalid! Must be exactly 11 digits")
        return UID
    context.user_data["uid"] = uid_text
    await update.message.reply_text(f"✅ UID {uid_text} verified\n\n👤 Step 2/4: FF ID Name")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("✅ Name saved\n\n📧 Step 3/4: Email")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "@" not in update.message.text:
        await update.message.reply_text("❌ Invalid email")
        return EMAIL
    context.user_data["email"] = update.message.text.strip()
    price = context.user_data["price"]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"🏦 OPay {ACCOUNT_NUMBER} - ₦{price}", callback_data="pay_opay")]])
    await update.message.reply_text(f"✅ Confirmed! TXN: `{context.user_data['txn']}`\n\n👇 Choose Payment:", reply_markup=kb)
    return PAYMENT_CHOICE

async def payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(f"💳 *OPay Payment*\nAcc: `{ACCOUNT_NUMBER}`\nName: {ACCOUNT_NAME}\nAmount: *₦{context.user_data['price']} EXACT*\n\nType *{context.user_data['price']}* after paying")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = context.user_data["price"]
    if str(price) not in update.message.text:
        await update.message.reply_text(f"❌ Type {price} EXACT!")
        return AMOUNT
    await update.message.reply_text("✅ Confirmed!\n\n📸 Upload OPay receipt")
    return RECEIPT

async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txn = context.user_data["txn"]
    user = update.effective_user
    db.execute("INSERT INTO orders(txn_id, user_id, username, ff_uid, ff_name, email, package, likes, amount, pay_method, status, date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
               (txn, user.id, user.username, context.user_data["uid"], context.user_data["name"], context.user_data["email"], context.user_data["pkg"], context.user_data["likes"], context.user_data["price"], "OPAY", "PENDING", datetime.now().strftime("%d-%m %H:%M")))
    db.commit()
    oid = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Affiliate commission
    row = db.execute("SELECT referrer_id FROM users WHERE user_id=?", (user.id,)).fetchone()
    if row and row[0]:
        ref_id = row[0]
        commission = int(context.user_data["price"] * 0.20)
        db.execute("UPDATE users SET balance=balance+?, total_earned=total_earned+? WHERE user_id=?", (commission, commission, ref_id))
        db.commit()
        try: await context.bot.send_message(ref_id, f"💰 Affiliate! You got ₦{commission}!")
        except: pass

    await update.message.reply_text(f"📦 *Order #{oid} | {txn}* ⏳ Received! Pending admin approval", reply_markup=main_menu())

    # Send to admin
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"ap_{user.id}_{oid}"), InlineKeyboardButton("❌ Reject", callback_data=f"rj_{user.id}_{oid}")]])
    try:
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"🔔 ORDER #{oid} | {txn}\n@{user.username} {user.id}\nUID:{context.user_data['uid']}\n📦 {context.user_data['likes']} Likes ₦{context.user_data['price']}", reply_markup=kb)
    except: pass

    return ConversationHandler.END

async def admin_act(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    act, uid, oid = update.callback_query.data.split("_")
    row = db.execute("SELECT likes, txn_id FROM orders WHERE id=?", (oid,)).fetchone()
    if not row: return
    likes, txn = row
    if act == "ap":
        db.execute("UPDATE orders SET status='DELIVERED' WHERE id=?", (oid,))
        db.commit()
        try: await context.bot.send_message(int(uid), f"✅ Order #{oid} | {txn} DELIVERED! 🎉 {likes} Likes Added!")
        except: pass
    else:
        db.execute("UPDATE orders SET status='REJECTED' WHERE id=?", (oid,))
        db.commit()
        try: await context.bot.send_message(int(uid), f"❌ Order #{oid} | {txn} Rejected")
        except: pass

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled", reply_markup=main_menu())
    return ConversationHandler.END

# FLASK FOR RENDER
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "LikeBot Alive 🔥"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

def build_application():
    req = HTTPXRequest