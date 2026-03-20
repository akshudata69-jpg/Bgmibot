import os, threading, logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# --- SETTINGS ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = "@AKSHARSTORE"

# --- STATES ---
ST_CHECK, ST_REP_USR, ST_REP_TYPE, ST_REP_PROOF, ST_REG, ST_BC = range(6)

# --- WEB SERVER (Render Health Check) ---
server = Flask(__name__)
@server.route('/')
def health(): return "SafeDeal Bot Active", 200
def run_s(): server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- MIDDLEWARE: FORCE JOIN ---
async def check_join(update, context):
    try:
        m = await context.bot.get_chat_member(CHANNEL_ID, update.effective_user.id)
        return m.status in ['member', 'administrator', 'creator']
    except: return False

# --- UI MENU ---
def main_menu(uid):
    kbd = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="m_check"), InlineKeyboardButton("🚨 Report Seller", callback_data="m_rep")],
        [InlineKeyboardButton("📸 Submit Proof", callback_data="m_rep"), InlineKeyboardButton("📝 Register as Seller", callback_data="m_reg")],
        [InlineKeyboardButton("🏆 Trusted Sellers", callback_data="m_top"), InlineKeyboardButton("🚫 Scammer List", callback_data="m_scam")],
        [InlineKeyboardButton("🛒 Buy Accounts", url="https://t.me/AKSHARSTORE"), InlineKeyboardButton("📊 My Activity", callback_data="m_me")]
    ]
    if uid == ADMIN_ID: kbd.append([InlineKeyboardButton("⚙️ ADMIN PANEL", callback_data="m_admin")])
    return InlineKeyboardMarkup(kbd)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_or_update_user(update.effective_user.id, update.effective_user.username or "Unknown")
    
    if not await check_join(update, context):
        kbd = [[InlineKeyboardButton("Join @AKSHARSTORE", url=f"https://t.me/{CHANNEL_ID[1:]}")],
               [InlineKeyboardButton("✅ I Joined, Check Again", callback_data="m_start")]]
        await update.message.reply_text("👋 **Welcome to SafeDeal Bot**\nYou must join our channel to use this bot.", reply_markup=InlineKeyboardMarkup(kbd))
        return ConversationHandler.END

    msg = "🔥 **SafeDeal Bot – BGMI Trust System**\nYour trusted platform to avoid scams.\n\nMade by @KING_HU_MAI"
    await update.message.reply_text(msg, reply_markup=main_menu(update.effective_user.id))
    return ConversationHandler.END

# --- FEATURE: CHECK SELLER ---
async def check_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔍 Send the **@username** of the seller:")
    return ST_CHECK

async def do_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.replace("@", "").strip()
    user = database.get_user(target)
    if not user:
        await update.message.reply_text("❓ **User not found.** They have no history here.")
    else:
        badge = "👑 VERIFIED" if user[5] else "👤 Standard"
        res = (f"👤 **User:** @{user[1]}\n"
               f"📊 **Trust Score:** {user[4]}\n"
               f"✅ Vouches: {user[3]} | 🚩 Reports: {user[2]}\n"
               f"📢 **Status:** {user[7]} {badge}")
        await update.message.reply_text(res, reply_markup=main_menu(update.effective_user.id))
    return ConversationHandler.END

# --- FEATURE: REPORT SYSTEM ---
async def report_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🚨 Send the **@username** of the scammer:")
    return ST_REP_USR

async def rep_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target'] = update.message.text.replace("@", "")
    kbd = [[InlineKeyboardButton("Scam", callback_data="r_scam"), InlineKeyboardButton("Fake Acc", callback_data="r_fake")],
           [InlineKeyboardButton("No Response", callback_data="r_ghost")]]
    await update.message.reply_text("Select Report Type:", reply_markup=InlineKeyboardMarkup(kbd))
    return ST_REP_TYPE

async def rep_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data['type'] = update.callback_query.data
    await update.callback_query.message.reply_text("📸 **PROOF REQUIRED.** Send a screenshot photo:")
    return ST_REP_PROOF

async def rep_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please send an actual photo.")
        return ST_REP_PROOF
    
    photo = update.message.photo[-1].file_id
    target = context.user_data['target']
    
    # Send to Admin for Approval
    kbd = [[InlineKeyboardButton("✅ Approve (+5 Vouch)", callback_data=f"adm_app_{target}"),
            InlineKeyboardButton("❌ Reject", callback_data="adm_rej")]]
    
    await context.bot.send_photo(ADMIN_ID, photo, 
                               caption=f"📥 **NEW REPORT**\nBy: @{update.effective_user.username}\nTarget: @{target}\nType: {context.user_data['type']}",
                               reply_markup=InlineKeyboardMarkup(kbd))
    
    await update.message.reply_text("✅ Report submitted! Admin will verify proofs.")
    return ConversationHandler.END

# --- ADMIN PANEL COMMANDS ---
async def admin_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target = context.args[0].replace("@", "")
        conn = sqlite3.connect('safedeal.db')
        conn.execute("UPDATE users SET is_verified = 1 WHERE username = ?", (target,))
        conn.commit()
        database.recalculate_score(target)
        await update.message.reply_text(f"👑 @{target} is now VERIFIED.")
    except: await update.message.reply_text("Usage: /verify @username")

# --- MAIN RUNNER ---
def main():
    database.init_db()
    threading.Thread(target=run_s, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(check_init, pattern="^m_check$"),
            CallbackQueryHandler(report_init, pattern="^m_rep$"),
            CallbackQueryHandler(start, pattern="^m_start$"),
        ],
        states={
            ST_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_check)],
            ST_REP_USR: [MessageHandler(filters.TEXT & ~filters.COMMAND, rep_user)],
            ST_REP_TYPE: [CallbackQueryHandler(rep_type, pattern="^r_")],
            ST_REP_PROOF: [MessageHandler(filters.PHOTO, rep_done)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", admin_verify))
    app.add_handler(conv)
    
    print("SafeDeal Bot: 100% ONLINE")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
