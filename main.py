import os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = "@AKSHARSTORE"

# --- STATES ---
ST_CHECK, ST_REP_USR, ST_REP_TYPE, ST_REP_PROOF = range(4)

# --- WEB SERVER (For Render/GCP) ---
server = Flask(__name__)
@server.route('/')
def h(): return "Bot Online", 200
def run_s(): server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- ACCESS CHECK ---
async def is_joined(update, context):
    try:
        m = await context.bot.get_chat_member(CHANNEL_ID, update.effective_user.id)
        return m.status in ['member', 'administrator', 'creator']
    except: return False

# --- KEYBOARD ---
def get_main_menu(uid):
    kbd = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="btn_check"), InlineKeyboardButton("🚨 Report Seller", callback_data="btn_report")],
        [InlineKeyboardButton("📸 Submit Proof", callback_data="btn_report"), InlineKeyboardButton("📝 Register Seller", callback_data="btn_reg")],
        [InlineKeyboardButton("🏆 Trusted Sellers", callback_data="btn_top"), InlineKeyboardButton("🚫 Scammer List", callback_data="btn_scam")],
        [InlineKeyboardButton("🛒 Buy Accounts", url="https://t.me/AKSHARSTORE"), InlineKeyboardButton("📊 My Activity", callback_data="btn_me")]
    ]
    if uid == ADMIN_ID: kbd.append([InlineKeyboardButton("👨‍💼 ADMIN PANEL", callback_data="btn_admin")])
    return InlineKeyboardMarkup(kbd)

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear() # Reset any stuck data
    if not await is_joined(update, context):
        kbd = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")],
               [InlineKeyboardButton("✅ Check Again", callback_data="btn_start")]]
        await (update.callback_query.message.edit_text if update.callback_query else update.message.reply_text)(
            "❌ **Join @AKSHARSTORE to use the bot!**", reply_markup=InlineKeyboardMarkup(kbd))
        return ConversationHandler.END

    msg = "🔥 **SafeDeal Bot – BGMI Marketplace**\nProtecting you from scammers.\n\nOwner: @KING_HU_MAI"
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=get_main_menu(update.effective_user.id))
    else:
        await update.message.reply_text(msg, reply_markup=get_main_menu(update.effective_user.id))
    return ConversationHandler.END

# --- CHECK SELLER ---
async def check_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔍 Send the **@username** of the seller:")
    return ST_CHECK

async def do_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.replace("@", "").strip()
    user = database.get_user(target)
    if not user:
        await update.message.reply_text("❓ User not found. No scam/vouch history.")
    else:
        badge = "👑 VERIFIED" if user[5] else "👤 Standard"
        res = (f"👤 **User:** @{user[1]}\n📊 **Score:** {user[4]}\n"
               f"✅ Vouches: {user[3]} | 🚩 Reports: {user[2]}\n📢 **Status:** {user[7]} {badge}")
        await update.message.reply_text(res, reply_markup=get_main_menu(update.effective_user.id))
    return ConversationHandler.END

# --- REPORT SYSTEM ---
async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🚨 Send the **@username** of the scammer:")
    return ST_REP_USR

async def report_user_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target'] = update.message.text.replace("@", "")
    kbd = [[InlineKeyboardButton("Scam", callback_data="r_scam"), InlineKeyboardButton("Fake ID", callback_data="r_fake")]]
    await update.message.reply_text("Select Reason:", reply_markup=InlineKeyboardMarkup(kbd))
    return ST_REP_TYPE

async def report_type_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['type'] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📸 Send **Photo Proof** (Screenshot):")
    return ST_REP_PROOF

async def report_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return ST_REP_PROOF
    target = context.user_data['target']
    photo = update.message.photo[-1].file_id
    
    # Send to Admin
    kbd = [[InlineKeyboardButton("✅ Approve (+5)", callback_data=f"adm_v_{target}"),
            InlineKeyboardButton("❌ Reject", callback_data="adm_rej")]]
    await context.bot.send_photo(ADMIN_ID, photo, caption=f"🚨 **REPORT**\nTarget: @{target}\nType: {context.user_data['type']}", reply_markup=InlineKeyboardMarkup(kbd))
    
    await update.message.reply_text("✅ Proof sent to Admin for approval!", reply_markup=get_main_menu(update.effective_user.id))
    return ConversationHandler.END

# --- MAIN ENGINE ---
def main():
    database.init_db()
    threading.Thread(target=run_s, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(check_entry, pattern="^btn_check$"),
            CallbackQueryHandler(report_entry, pattern="^btn_report$"),
            CallbackQueryHandler(start, pattern="^btn_start$"),
        ],
        states={
            ST_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_check)],
            ST_REP_USR: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_user_recv)],
            ST_REP_TYPE: [CallbackQueryHandler(report_type_recv, pattern="^r_")],
            ST_REP_PROOF: [MessageHandler(filters.PHOTO, report_done)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True # CRITICAL: Allows switching between buttons
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    
    print("Bot is 100% operational.")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
