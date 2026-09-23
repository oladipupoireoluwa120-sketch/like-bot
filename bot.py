import sqlite3, warnings, re, asyncio, os, random, string
warnings.filterwarnings("ignore")
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler, ChatMemberHandler
from telegram.request import HTTPXRequest
from telegram.constants import ChatMemberStatus

BOT_TOKEN = "8767564803:AAGeeWoT-1TeRZsSOTTeg420JxYW2FvHOdc"
ADMIN_ID = 8805633124
SUPPORT_USERNAME = "MARCUSSUPPORT"
ACCOUNT_NUMBER = "6143597127"
ACCOUNT_NAME = "IREOLUWA SAMUEL OLADIPUPO"

# ====== BOTH CHANNELS ======
FORCE_CHANNEL = "@likebotofficial"
FORCE_CHANNEL_ID = -1004432894885
PROOF_CHANNEL = "@likebotbackup"
PROOF_CHANNEL_ID = -1003887562036
# ===========================

PACKAGES = {
    "1000": {"likes": 1000, "price": 100, "label": "1000 Likes - ₦100 🔥"},
    "3000": {"likes": 3000, "price": 250, "label": "3000 Likes - ₦250 ⭐ BEST"},
    "5000": {"likes": 5000, "price": 400, "label": "5000 Likes - ₦400 💎"},
    "10000": {"likes": 10000, "price": 700, "label": "10000 Likes - ₦700 👑 MEGA"},
    "upsell_2000": {"likes": 2000, "price": 150, "label": "Add 2000 Likes - ₦150 🔥"}
}

request = HTTPXRequest(connect_timeout=60, read_timeout=60, write_timeout=60, pool_timeout=60)
UID, NAME, EMAIL, PAYMENT_CHOICE, AMOUNT, RECEIPT = range(6)
START_TIME = datetime(2026, 1, 1)

db = sqlite3.connect("orders.db", check_same_thread=False)
db.execute("""CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, username TEXT, referrer_id INTEGER, referrals_count INTEGER DEFAULT 0, balance INTEGER DEFAULT 0, total_earned INTEGER DEFAULT 0, joined TEXT, total_orders INTEGER DEFAULT 0, fake_attempts INTEGER DEFAULT 0, banned INTEGER DEFAULT 0)""")
db.execute("""CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, txn_id TEXT, user_id INTEGER, username TEXT, ff_uid TEXT, ff_name TEXT, email TEXT, package TEXT, likes INTEGER, amount INTEGER, pay_method TEXT, status TEXT, date TEXT)""")
db.execute("""CREATE TABLE IF NOT EXISTS referrals(id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER, referred_id INTEGER, date TEXT)""")
db.execute("""CREATE TABLE IF NOT EXISTS carts(user_id INTEGER PRIMARY KEY, pkg TEXT, price INTEGER, created TEXT)""")
db.commit()

def gen_txn(): return f"LB-{''.join(random.choices(string.digits, k=5))}{random.choice(string.ascii_uppercase)}"
def get_live_count():
    real = db.execute("SELECT COUNT(*) FROM orders WHERE status='DELIVERED'").fetchone()[0]
    hours = int((datetime.now() - START_TIME).total_seconds() / 7200)
    return 150 + real + hours
def get_ticker():
    row = db.execute("SELECT ff_name, likes FROM orders WHERE status='DELIVERED' ORDER BY id DESC LIMIT 1").fetchone()
    if row: return f"🔥 {row[0]} just got {row[1]} likes 2m ago!"
    return "🔥 @Tunde just bought 3000 likes 3m ago!"
def main_menu():
    return ReplyKeyboardMarkup([["🚀 BOOST LIKES", "💰 PACKAGES"],["👥 REFER & EARN 20%", "💳 MY BALANCE - REFER & EARN"],["📋 MY ORDERS", "🏆 TOP REFERRERS"],["ℹ️ HOW IT WORKS", "💬 SUPPORT"],["⭐ REVIEWS", "💳 PAYMENT"]], resize_keyboard=True, is_persistent=True)

# Feature 2: Typing animation helper
async def typing(bot, chat_id):
    try:
        await bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(1)
    except: pass

async def check_joined(user_id, bot):
    try:
        m1 = await bot.get_chat_member(FORCE_CHANNEL_ID, user_id)
        ok1 = m1.status in ['member','administrator','creator']
    except: ok1 = False
    try:
        m2 = await bot.get_chat_member(PROOF_CHANNEL_ID, user_id)
        ok2 = m2.status in ['member','administrator','creator']
    except: ok2 = False
    return (ok1 and ok2), ok1, ok2

def ensure_user(u):
    if not db.execute("SELECT user_id FROM users WHERE user_id=?", (u.id,)).fetchone():
        db.execute("INSERT INTO users(user_id, username, joined) VALUES(?,?,?)", (u.id, u.username, datetime.now().strftime("%d-%m-%Y"))); db.commit()
    banned = db.execute("SELECT banned FROM users WHERE user_id=?", (u.id,)).fetchone()
    return banned and banned[0]==1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await typing(context.bot, user.id)
    joined_both, ok1, ok2 = await check_joined(user.id, context.bot)
    if not joined_both:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{'✅' if ok1 else '❌'} JOIN LIKEBOT OFFICIAL🔥", url=f"https://t.me/likebotofficial")],
            [InlineKeyboardButton(f"{'✅' if ok2 else '❌'} JOIN LIKEBOT BACKUP🥂", url=f"https://t.me/likebotbackup")],
            [InlineKeyboardButton("✅ I Joined Both - Verify", callback_data="check_join")]
        ])
        await update.message.reply_text(f"⚠️ *JOIN BOTH CHANNELS TO USE BOT* 🔒🔒\n\nYou must join BOTH channels!\n\nOfficial: {'✅ Joined' if ok1 else '❌ Not Joined'}\nBackup: {'✅ Joined' if ok2 else '❌ Not Joined'}\n\n👇 Join both then click Verify ✅\n\n🛡️ Anti-Scam: Only @MARCUSSUPPORT is real.", parse_mode=None, reply_markup=kb)
        return
    if ensure_user(user): await update.message.reply_text("🚫 Banned. DM @MARCUSSUPPORT"); return
    ensure_user(user)
    if context.args and context.args[0].startswith("REF"):
        try:
            rid = int(context.args[0].replace("REF",""))
            if rid!=user.id and not db.execute("SELECT * FROM referrals WHERE referred_id=?", (user.id,)).fetchone():
                cur = db.execute("SELECT referrer_id FROM users WHERE user_id=?", (user.id,)).fetchone()
                if cur and cur[0] is None:
                    db.execute("INSERT INTO referrals(referrer_id, referred_id, date) VALUES(?,?,?)", (rid, user.id, datetime.now().strftime("%d-%m")))
                    db.execute("UPDATE users SET referrals_count=referrals_count+1 WHERE user_id=?", (rid,))
                    db.execute("UPDATE users SET referrer_id=? WHERE user_id=?", (rid, user.id)); db.commit()
        except: pass
    live = get_live_count(); ticker = get_ticker()
    await update.message.reply_text(f"🔥 *LIKEBOT OFFICIAL* ✅ Verified\n{ticker} ⚡\n✅ Joined Both ✅\n━━━━━━━━━━━━━━━━━━\n✅ *{live}+ Delivered* 📦\n🛡️ *100% Money-Back 30 mins* ✅\n✅ Verified by @{SUPPORT_USERNAME} 👑\n\n📢 @likebotofficial | 📦 @likebotbackup\n\n👇 *Tap Menu Below* ⭐", parse_mode=None, reply_markup=main_menu())

async def check_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await typing(context.bot, update.effective_user.id)
    joined_both, ok1, ok2 = await check_joined(update.effective_user.id, context.bot)
    if joined_both:
        try: await update.callback_query.message.delete()
        except: pass
        await start(update, context)
    else:
        await update.callback_query.answer(f"❌ Not joined both! Official: {'✅' if ok1 else '❌'} | Backup: {'✅' if ok2 else '❌'}", show_alert=True)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined_both, ok1, ok2 = await check_joined(update.effective_user.id, context.bot)
    if not joined_both:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{'✅' if ok1 else '❌'} Join @likebotofficial", url=f"https://t.me/likebotofficial")],[InlineKeyboardButton(f"{'✅' if ok2 else '❌'} Join @likebotbackup", url=f"https://t.me/likebotbackup")],[InlineKeyboardButton("✅ I Joined Both - Verify", callback_data="check_join")]])
        await update.message.reply_text(f"🔒 Join BOTH first!\nOfficial: {'✅' if ok1 else '❌'}\nBackup: {'✅' if ok2 else '❌'}", reply_markup=kb); return
    await typing(context.bot, update.effective_user.id)
    txt = update.message.text; uid = update.effective_user.id
    if ensure_user(update.effective_user): return
    low = txt.lower()
    if any(w in low for w in ["scam", "fake", "legit", "real"]):
        await update.message.reply_text("⭐ *Is it legit?* ✅\n\n📊 150+ Delivered\n⭐ 4.3/5.0\n🛡️ Money-back\n✅ Verified by @MARCUSSUPPORT\n\n📢 Main: @likebotofficial\n📦 Proofs: @likebotbackup", parse_mode=None, reply_markup=main_menu()); return
    if "how long" in low: await update.message.reply_text("⏱️ Delivery: 5-10 mins ✅\n🛡️ 30 mins money-back!\n📦 Proofs: @likebotbackup", reply_markup=main_menu()); return
    if txt in ["🚀 BOOST LIKES", "💰 PACKAGES"]:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 1000 Likes - ₦100", callback_data="pkg_1000")],[InlineKeyboardButton("⭐ 3000 Likes - ₦250 [BEST]", callback_data="pkg_3000")],[InlineKeyboardButton("💎 5000 Likes - ₦400", callback_data="pkg_5000")],[InlineKeyboardButton("👑 10000 Likes - ₦700 MEGA", callback_data="pkg_10000")]])
        await update.message.reply_text(f"💰 *SELECT PACKAGE* 👇\n🛡️ Money-Back ✅\n✅ Verified", parse_mode=None, reply_markup=kb); return
    if txt == "👥 REFER & EARN 20%":
        c,b,e = db.execute("SELECT referrals_count, balance, total_earned FROM users WHERE user_id=?", (uid,)).fetchone()
        botname = (await context.bot.get_me()).username; link = f"https://t.me/{botname}?start=REF{uid}"
        await update.message.reply_text(f"👥 *EARN 20% PER FRIEND* 💸\n━━━━━━━━━━━━━━━\n🔗 Link:\n`{link}`\n\n📊 Refs: {c}\n💰 Balance: ₦{b}\n💸 Earned: ₦{e}\n\n🎁 20% per sale + ₦500 every 3 refs!", parse_mode=None, reply_markup=main_menu()); return
    if txt == "💳 MY BALANCE - REFER & EARN":
        bal, count, earn = db.execute("SELECT balance, referrals_count, total_earned FROM users WHERE user_id=?", (uid,)).fetchone()
        await update.message.reply_text(f"💳 *MY BALANCE* 💰\n💰 Balance: *₦{bal}*\n👥 Refs: {count}\n💸 Earned: ₦{earn}\n✅ Verified", parse_mode=None, reply_markup=main_menu()); return
    if txt == "📋 MY ORDERS":
        rows = db.execute("SELECT id, txn_id, likes, status, date FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 7", (uid,)).fetchall()
        if not rows: await update.message.reply_text("📋 No orders yet!", reply_markup=main_menu())
        else:
            msg = "📋 *YOUR ORDERS + TXN ID* 📦\n━━━━━━━━━━━━━━━\n"
            for oid, txn, likes, st, date in rows:
                ic = "✅" if st=="DELIVERED" else "⏳"; msg+=f"{ic} #{oid} | {txn} | {likes} Likes | {st}\n"
            await update.message.reply_text(msg, parse_mode=None, reply_markup=main_menu())
        return
    if txt == "🏆 TOP REFERRERS":
        rows = db.execute("SELECT username, referrals_count FROM users ORDER BY referrals_count DESC LIMIT 5").fetchall()
        msg = "🏆 *TOP REFERRERS - SUNDAY ₦200 BONUS* 👑\n"
        for i,(uname, cnt) in enumerate(rows,1): msg+=f"{i}. @{uname or 'user'} - {cnt} refs\n"
        await update.message.reply_text(msg, parse_mode=None, reply_markup=main_menu()); return
    if txt == "⭐ REVIEWS":
        await update.message.reply_text("⭐ *REVIEWS* ⭐\n━━━━━━━━━━━━━━━\n\n👤 @James_ff_01 - 2h ago\n⭐⭐⭐⭐⭐ 5.0\n\"Omo this bot legit die! 😭\"\n📦 1000 Likes ✅ TXN: LB-1234A\n\n👤 @Bliss_gaming - Yesterday\n⭐⭐⭐⭐ 4.0\n\"I was scared at first but my account is now at 3k likes. Thank you @MARCUSSUPPORT for the great service.\"\n📦 3000 Likes ✅\n\n👤 @MusaPro - 2 days ago\n⭐⭐⭐½ 3.5\n\"Best booster for Naija.\"\n📦 5000 Likes ✅\n\n👤 @Queen_Amarachi - 3 days ago\n⭐⭐⭐⭐⭐ 5.0\n\"I just use it for the referral 🤭\"\n📦 Referral ✅\n\n👤 @Khalid_yt - 5 days ago\n⭐⭐⭐⭐ 4.0\n\"just get the 10k like plan will save you stress\"\n📦 10000 Likes ✅\n\n📊 150+ Delivered | ✅ Verified", parse_mode=None, reply_markup=main_menu()); return
    if txt in ["ℹ️ HOW IT WORKS","💬 SUPPORT","💳 PAYMENT"]:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💬 DM @MARCUSSUPPORT 👑", url=f"https://t.me/MARCUSSUPPORT")],[InlineKeyboardButton(f"📢 Main", url=f"https://t.me/likebotofficial")],[InlineKeyboardButton(f"📦 Proof", url=f"https://t.me/likebotbackup")]])
        await update.message.reply_text(f"💬 Support: @MARCUSSUPPORT ✅ Verified\n🏦 OPay {ACCOUNT_NUMBER}\n🛡️ 100% Money-Back\n📢 @likebotofficial | 📦 @likebotbackup", reply_markup=kb); return

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined_both, ok1, ok2 = await check_joined(update.effective_user.id, context.bot)
    if not joined_both: await update.callback_query.answer(f"Join BOTH! Official: {'✅' if ok1 else '❌'} Backup: {'✅' if ok2 else '❌'}", show_alert=True); return
    await update.callback_query.answer()
    await typing(context.bot, update.effective_user.id)
    pkg_id = update.callback_query.data.replace("pkg_","")
    if pkg_id.startswith("upsell"): context.user_data["pkg"] = "2000"; context.user_data["likes"] = 2000; context.user_data["price"] = 150
    else: pkg = PACKAGES[pkg_id]; context.user_data["pkg"] = pkg_id; context.user_data["likes"] = pkg["likes"]; context.user_data["price"] = pkg["price"]
    db.execute("INSERT OR REPLACE INTO carts(user_id, pkg, price, created) VALUES(?,?,?,?)", (update.effective_user.id, context.user_data["pkg"], context.user_data["price"], datetime.now().isoformat())); db.commit()
    txn = gen_txn(); context.user_data["txn"] = txn
    await update.callback_query.message.reply_text(f"✅ *{context.user_data['likes']} Likes - ₦{context.user_data['price']}* Selected! 🎉\n🆔 TXN: `{txn}`\n\n🎮 Step 1/4: Send Free Fire UID 🔢\n⚠️ *EXACTLY 11 digits*", parse_mode=None)
    return UID

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(context.bot, update.effective_user.id)
    uid_text = update.message.text.strip()
    if not uid_text.isdigit() or len(uid_text)!=11: await update.message.reply_text(f"❌ Invalid! Must be exactly 11 digits"); return UID
    pending_same = db.execute("SELECT id FROM orders WHERE ff_uid=? AND status='PENDING'", (uid_text,)).fetchone()
    if pending_same: await update.message.reply_text(f"⚠️ UID {uid_text} has pending order #{pending_same[0]} ⏳ Wait!"); return ConversationHandler.END
    context.user_data["uid"] = uid_text; await update.message.reply_text(f"✅ UID {uid_text} verified ✅\n\n👤 Step 2/4: FF ID Name"); return NAME
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(context.bot, update.effective_user.id)
    context.user_data["name"] = update.message.text.strip(); await update.message.reply_text("✅ Name saved\n\n📧 Step 3/4: Email"); return EMAIL
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(context.bot, update.effective_user.id)
    if "@" not in update.message.text: await update.message.reply_text("❌ Invalid email"); return EMAIL
    context.user_data["email"] = update.message.text.strip()
    price = context.user_data["price"]; bal = db.execute("SELECT balance FROM users WHERE user_id=?", (update.effective_user.id,)).fetchone()[0]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Balance ₦{bal}", callback_data="pay_bal")],[InlineKeyboardButton(f"🏦 OPay {ACCOUNT_NUMBER} - ₦{price}", callback_data="pay_opay")]])
    await update.message.reply_text(f"✅ Confirmed! TXN: `{context.user_data['txn']}`\nUID: {context.user_data['uid']}\nPackage: {context.user_data['likes']} Likes - ₦{price}\n\n👇 Choose Payment:", parse_mode=None, reply_markup=kb)
    return PAYMENT_CHOICE
async def handle_affiliate(buyer_id, amount, context):
    row = db.execute("SELECT referrer_id FROM users WHERE user_id=?", (buyer_id,)).fetchone()
    if row and row[0]:
        ref_id = row[0]; commission = int(amount * 0.20)
        db.execute("UPDATE users SET balance=balance+?, total_earned=total_earned+? WHERE user_id=?", (commission, commission, ref_id)); db.commit()
        try: await context.bot.send_message(ref_id, f"💰 *Affiliate!* 🎉\nFriend bought ₦{amount} = You got ₦{commission} (20%)!")
        except: pass

async def payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await typing(context.bot, update.effective_user.id)
    choice = update.callback_query.data; price = context.user_data["price"]; likes = context.user_data["likes"]; uid_text = context.user_data["uid"]; name = context.user_data["name"]; email = context.user_data["email"]; user = update.effective_user; date = datetime.now().strftime("%d-%m %H:%M"); txn = context.user_data.get("txn", gen_txn())
    db.execute("DELETE FROM carts WHERE user_id=?", (user.id,)); db.commit()
    if choice == "pay_bal":
        bal = db.execute("SELECT balance FROM users WHERE user_id=?", (user.id,)).fetchone()[0]
        if bal < price: await update.callback_query.message.reply_text(f"❌ Balance low", reply_markup=main_menu()); return ConversationHandler.END
        db.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (price, user.id))
        db.execute("INSERT INTO orders(txn_id, user_id, username, ff_uid, ff_name, email, package, likes, amount, pay_method, status, date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(txn, user.id, user.username, uid_text, name, email, context.user_data["pkg"], likes, price, "BALANCE", "PENDING", date)); db.commit()
        oid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        await handle_affiliate(user.id, price, context)
        m1 = await update.callback_query.message.reply_text(f"📦 *Order #{oid} | {txn}* ⏳\n✅ Balance Paid\n🚀 Sending... 0%", parse_mode=None)
        # Feature 2: Progress bar animation
        for p in [10, 40, 80, 100]:
            await asyncio.sleep(0.8)
            try: await context.bot.edit_message_text(f"📦 *Order #{oid} | {txn}* ⏳\n🚀 Sending... {p}%\n{'▓'* (p//10)}{'░'*(10-p//10)}", chat_id=m1.chat_id, message_id=m1.message_id, parse_mode=None)
            except: pass
        db.execute("UPDATE orders SET status='DELIVERED' WHERE id=?", (oid,)); db.commit()
        await context.bot.edit_message_text(f"📦 *Order #{oid} | {txn} DELIVERED ✅* 🎉\n✅ {likes} Likes to {uid_text}!\n✅ Verified by @{SUPPORT_USERNAME}\n📧 Email to {email}", chat_id=m1.chat_id, message_id=m1.message_id, parse_mode=None)
        # Feature 9: Screenshot button
        share_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📸 Share Proof + Get ₦20", callback_data=f"share_{oid}")],
            [InlineKeyboardButton(f"🔥 Add 2000 More for ₦150?", callback_data="pkg_upsell_2000")]
        ])
        await context.bot.send_message(user.id, f"🎉 *Delivered!* Want ₦20 free?\n\n📸 Screenshot your FF likes & share to WhatsApp status\nTag @likebotofficial\nThen click below to claim ₦20!", parse_mode=None, reply_markup=share_kb)
        try:
            await context.bot.send_message(PROOF_CHANNEL_ID, f"✅ *DELIVERED* | TXN: {txn}\n📦 {likes} Likes to {uid_text[:3]}***{uid_text[-3:]}\n💰 ₦{price} via Balance\n👤 {name}\n⏱️ {date}")
            await context.bot.send_message(FORCE_CHANNEL_ID, f"🔥 *NEW DELIVERY* 🔥\n✅ {likes} Likes to {name}!\n💰 ₦{price}\nTXN: {txn}\n📦 Proof: @likebotbackup")
        except: pass
        return ConversationHandler.END
    else:
        await update.callback_query.message.reply_text(f"💳 *OPay* 🏦\nAcc: `{ACCOUNT_NUMBER}`\nName: {ACCOUNT_NAME}\nAmount: *₦{price} EXACT*\nTXN: `{txn}`\n\nType *{price}* after paying", parse_mode=None)
        return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(context.bot, update.effective_user.id)
    price = context.user_data["price"]
    if str(price) not in update.message.text:
        db.execute("UPDATE users SET fake_attempts=fake_attempts+1 WHERE user_id=?", (update.effective_user.id,)); db.commit()
        attempts = db.execute("SELECT fake_attempts FROM users WHERE user_id=?", (update.effective_user.id,)).fetchone()[0]
        if attempts >= 3: db.execute("UPDATE users SET banned=1 WHERE user_id=?", (update.effective_user.id,)); db.commit(); await update.message.reply_text(f"🚫 BANNED! 3 fake attempts!"); return ConversationHandler.END
        await update.message.reply_text(f"❌ Type {price} EXACT! Attempt {attempts}/3"); return AMOUNT
    db.execute("UPDATE users SET fake_attempts=0 WHERE user_id=?", (update.effective_user.id,)); db.commit()
    await update.message.reply_text(f"✅ ₦{price} confirmed! TXN: {context.user_data['txn']}\n\n📸 Upload OPay receipt 🧾")
    return RECEIPT

async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(context.bot, update.effective_user.id)
    user = update.effective_user; price = context.user_data["price"]; likes = context.user_data["likes"]; uid_text = context.user_data["uid"]; name = context.user_data["name"]; email = context.user_data["email"]; date = datetime.now().strftime("%d-%m %H:%M"); txn = context.user_data.get("txn", gen_txn())
    db.execute("INSERT INTO orders(txn_id, user_id, username, ff_uid, ff_name, email, package, likes, amount, pay_method, status, date) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(txn, user.id, user.username, uid_text, name, email, context.user_data["pkg"], likes, price, "OPAY", "PENDING", date)); db.commit(); oid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("DELETE FROM carts WHERE user_id=?", (user.id,)); db.commit()
    await handle_affiliate(user.id, price, context)
    await update.message.reply_text(f"📦 *Order #{oid} | {txn}* ⏳\n✅ Receipt Received\n⏳ AI checking... 🤖\n✅ Verified\n📧 Email to {email} when delivered!", parse_mode=None, reply_markup=main_menu())
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"ap_{user.id}_{oid}"), InlineKeyboardButton("❌ Reject", callback_data=f"rj_{user.id}_{oid}")]])
    await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"🔔 ORDER #{oid} | {txn}\n@{user.username} {user.id}\nUID:{uid_text}\n📦 {likes} Likes ₦{price}\nTXN:{txn}", reply_markup=kb)
    return ConversationHandler.END

# Feature 9: Screenshot reward
async def share_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    oid = int(update.callback_query.data.replace("share_",""))
    user_id = update.effective_user.id
    # Give ₦20
    db.execute("UPDATE users SET balance=balance+20, total_earned=total_earned+20 WHERE user_id=?", (user_id,)); db.commit()
    bal = db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()[0]
    await update.callback_query.message.reply_text(f"🎉 Thanks for sharing! 📸\n\n✅ ₦20 added!\n💰 New Balance: ₦{bal}\n\nKeep sharing = Keep earning! 🚀\n📢 @likebotofficial | 📦 @likebotbackup", reply_markup=main_menu())
    try:
        await context.bot.send_message(PROOF_CHANNEL_ID, f"📸 *User Shared Proof!* Order #{oid}\n@{update.effective_user.username} shared delivery proof!\nRewarded ₦20 ✅\n📢 @likebotofficial")
    except: pass

# Feature 11: Failed payment reminder job
async def remind_failed_payment(context: ContextTypes.DEFAULT_TYPE):
    uid = context.job.data["user_id"]
    txn = context.job.data["txn"]
    try:
        await context.bot.send_message(uid, f"😢 Your Order {txn} was rejected ❌\n\n🔄 *Correct OPay Details:*\n🏦 Acc: `{ACCOUNT_NUMBER}`\nName: {ACCOUNT_NAME}\n\nMake sure amount is EXACT & receipt is clear!\n\nTap 🚀 BOOST LIKES to try again! ⚡\n💬 Need help? @MARCUSSUPPORT", parse_mode=None)
    except: pass

async def admin_act(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    act, uid, oid = update.callback_query.data.split("_")
    row = db.execute("SELECT ff_uid, email, likes, txn_id, amount, ff_name FROM orders WHERE id=?", (oid,)).fetchone()
    if not row: return
    ff_uid, email, likes, txn, amount, ff_name = row
    if act=="ap":
        try:
            m1 = await context.bot.send_message(int(uid), f"📦 *Order #{oid} | {txn}* ⏳\n✅ Payment Confirmed! Verified ✅\n🚀 Sending... 0%", parse_mode=None)
            for p in [10, 40, 80, 100]:
                await asyncio.sleep(0.8)
                try: await context.bot.edit_message_text(f"📦 *Order #{oid} | {txn}* ⏳\n🚀 Sending... {p}%\n{'▓'* (p//10)}{'░'*(10-p//10)}", chat_id=m1.chat_id, message_id=m1.message_id, parse_mode=None)
                except: pass
            db.execute("UPDATE orders SET status='DELIVERED' WHERE id=?", (oid,)); db.commit()
            await context.bot.send_message(int(uid), f"✅ *Order #{oid} | {txn} DELIVERED!* 🎉\n🎮 UID: {ff_uid}\n👑 {likes} Likes Added!\n✅ Verified\n📧 Email to {email}!\n📢 @likebotofficial", parse_mode=None)
            share_kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"📸 Share Proof + Get ₦20", callback_data=f"share_{oid}")],[InlineKeyboardButton(f"🔥 Add 2000 More for ₦150?", callback_data="pkg_upsell_2000")]])
            await context.bot.send_message(int(uid), f"🎉 *Want ₦20 free?* 📸\nScreenshot your likes & share to status!\nTag @likebotofficial then claim!", parse_mode=None, reply_markup=share_kb)
            try:
                await context.bot.send_message(PROOF_CHANNEL_ID, f"✅ *DELIVERED* | TXN: {txn}\n👤 {ff_name} | UID {ff_uid[:3]}***{ff_uid[-3:]}\n📦 {likes} Likes | ₦{amount}\n⏱️ {datetime.now().strftime('%d-%m %H:%M')}\n✅ Verified\n📢 @likebotofficial | 📦 @likebotbackup")
                await context.bot.send_message(FORCE_CHANNEL_ID, f"🔥 *NEW DELIVERY* 🔥\n✅ {likes} Likes to {ff_name}!\n💰 ₦{amount}\nTXN: {txn}\n📦 Proof: @likebotbackup")
            except: pass
        except: pass
        try: await update.callback_query.edit_message_caption(caption=update.callback_query.message.caption + f"\n✅ APPROVED {txn}")
        except: pass
    else:
        db.execute("UPDATE orders SET status='REJECTED' WHERE id=?", (oid,)); db.commit()
        await context.bot.send_message(int(uid), f"❌ Order #{oid} | {txn} Rejected 😢 Wrong receipt.\n\n⏰ I will remind you in 1 min with correct details...")
        # Feature 11: Remind after 1 min
        context.job_queue.run_once(remind_failed_payment, 60, data={"user_id": int(uid), "txn": txn})

# Feature 12: Channel welcome
async def channel_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.chat_member.new_chat_member.status == ChatMemberStatus.MEMBER:
            user = update.chat_member.new_chat_member.user
            if user.is_bot: return
            # Only welcome in your channels
            if update.chat_member.chat.id in [FORCE_CHANNEL_ID, PROOF_CHANNEL_ID]:
                await context.bot.send_message(
                    update.chat_member.chat.id,
                    f"🎉 Welcome {user.mention_html()} to {update.chat_member.chat.title}! 🔥\n\n💎 Buy Free Fire likes @{(await context.bot.get_me()).username} 🚀\n⭐ 1000 Likes - ₦100\n📦 Proofs here daily!\n\n👥 Refer friends = Earn 20% 💰",
                    parse_mode="HTML"
                )
    except: pass

async def abandoned_cart_job(context: ContextTypes.DEFAULT_TYPE):
    rows = db.execute("SELECT user_id, pkg, price, created FROM carts").fetchall()
    for uid, pkg, price, created in rows:
        try:
            created_dt = datetime.fromisoformat(created)
            if datetime.now() - created_dt > timedelta(minutes=5):
                likes = PACKAGES.get(pkg, {}).get("likes", pkg)
                await context.bot.send_message(uid, f"😢 You forgot your likes!\n📦 You selected {likes} Likes for ₦{price}\nStill want it? Tap 🚀 BOOST LIKES! ⚡\n📢 @likebotofficial")
                db.execute("DELETE FROM carts WHERE user_id=?", (uid,)); db.commit()
        except: pass

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%d-%m")
    total_today = db.execute("SELECT COUNT(*) FROM orders WHERE date LIKE?", (f"{today}%",)).fetchone()[0]
    rev_today = db.execute("SELECT SUM(amount) FROM orders WHERE date LIKE? AND status='DELIVERED'", (f"{today}%",)).fetchone()[0] or 0
    await context.bot.send_message(ADMIN_ID, f"📊 *DAILY REPORT* {today}\nOrders: {total_today}\nRevenue: ₦{rev_today}\nLive: {get_live_count()}+\n📢 @likebotofficial | 📦 @likebotbackup")
    try: await context.bot.send_document(ADMIN_ID, open("orders.db","rb"), caption=f"💾 Backup {today}")
    except: pass

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    msg = " ".join(context.args)
    for (uid_,) in db.execute("SELECT user_id FROM users").fetchall():
        try: await context.bot.send_message(uid_, f"📢 *LIKEBOT OFFICIAL* 🚀\n\n{msg}\n✅ Verified\n📢 @likebotofficial | 📦 @likebotbackup", parse_mode=None); await asyncio.sleep(0.07)
        except: pass

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.execute("DELETE FROM carts WHERE user_id=?", (update.effective_user.id,)); db.commit()
    await update.message.reply_text("❌ Cancelled", reply_markup=main_menu())
    return ConversationHandler.END

app = Application.builder().token(BOT_TOKEN).request(request).get_updates_request(request).build()
conv = ConversationHandler(entry_points=[CallbackQueryHandler(select_package, pattern="^pkg_")], states={UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_uid)], NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)], EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)], PAYMENT_CHOICE: [CallbackQueryHandler(payment_choice, pattern="^pay_")], AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)], RECEIPT: [MessageHandler(filters.PHOTO, get_receipt)]}, fallbacks=[CommandHandler("cancel", cancel)])
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_join_cb, pattern="check_join"))
app.add_handler(CallbackQueryHandler(share_reward, pattern="^share_"))
app.add_handler(MessageHandler(filters.Regex("^(🚀 BOOST LIKES|💰 PACKAGES|👥 REFER & EARN 20%|💳 MY BALANCE - REFER & EARN|📋 MY ORDERS|🏆 TOP REFERRERS|ℹ️ HOW IT WORKS|💬 SUPPORT|⭐ REVIEWS|💳 PAYMENT)$"), menu_handler))
app.add_handler(CallbackQueryHandler(select_package, pattern="^pkg_"))
app.add_handler(CallbackQueryHandler(payment_choice, pattern="^pay_"))
app.add_handler(CallbackQueryHandler(admin_act, pattern="^(ap_|rj_)"))
app.add_handler(ChatMemberHandler(channel_welcome, ChatMemberHandler.CHAT_MEMBER))
app.add_handler(conv)
app.add_handler(CommandHandler("broadcast", broadcast))
app.job_queue.run_repeating(daily_report, interval=86400, first=10)
app.job_queue.run_repeating(abandoned_cart_job, interval=300, first=300)
print(f"🔥 V6 - 2,9,11,12 ADDED - BOTH FORCE - Typing + Share ₦20 + Reminder + Welcome")
app.run_polling(drop_pending_updates=True)
