import os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# States
(S_CHECK, S_REP_USR, S_REP_AMT, S_REP_PRF, S_REG_USR, S_REG_CH, S_REG_DL, S_BC) = range(8)

# Flask for Render
server = Flask(__name__)
@server.route('/')
def h(): return "SafeDeal Live", 200
def run_s(): server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Check Seller", callback_data="m_check"), InlineKeyboardButton("🚨 Report Seller", callback_data="m_report")],
        [InlineKeyboardButton("📝 Register as Seller", callback_data="m_reg")],
        [InlineKeyboardButton("🚫 Scammer List", callback_data="m_list")],
        [InlineKeyboardButton("📢 Broadcast (Admin)", callback_data="m_bc")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_to_db("users", update.effective_user.id)
    context.user_data.clear()
    msg = "🛡️ **SafeDeal Marketplace**\nProtecting your trades."
    if update.callback_query: await update.callback_query.message.edit_text(msg, reply_markup=main_menu())
    else: await update.message.reply_text(msg, reply_markup=main_menu())
    return ConversationHandler.END

# --- REPORT FLOW ---
async def rep_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🚨 Enter Scammer's @username:")
    return S_REP_USR

async def rep_usr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['scam_user'] = update.message.text
    await update.message.reply_text("💰 Amount Scammed?")
    return S_REP_AMT

async def rep_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['scam_amt'] = update.message.text
    await update.message.reply_text("📸 Send Photo Proof (Screenshot):")
    return S_REP_PRF

async def rep_prf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return S_REP_PRF
    fid = update.message.photo[-1].file_id
    data = context.user_data
    await context.bot.send_photo(ADMIN_ID, fid, caption=f"🚨 **REPORT**\nUser: {data['scam_user']}\nAmount: {data['scam_amt']}\nBy: @{update.effective_user.username}")
    await update.message.reply_text("✅ Sent to Admin for approval!", reply_markup=main_menu())
    return ConversationHandler.END

# --- CHECK USER ---
async def check_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🔍 Send @username to check:")
    return S_CHECK

async def do_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.text.replace("@","")
    scam, sell = database.check_user(user)
    if scam:
        await update.message.reply_text(f"❌ **SCAMMER ALERT!**\nUser: @{scam[0]}\nAmount: {scam[1]}")
        await context.bot.send_photo(update.effective_chat.id, scam[2], caption="📄 **SCAM PROOF**")
    elif sell:
        await update.message.reply_text(f"✅ **VERIFIED SELLER**\nUser: @{sell[0]}\nDeals: {sell[2]}\nChannel: {sell[1]}")
    else:
        await update.message.reply_text("❓ Not in database.", reply_markup=main_menu())
    return ConversationHandler.END

# --- REGISTRATION ---
async def reg_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📝 Your @username:")
    return S_REG_USR

async def reg_usr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['r_user'] = update.message.text
    await update.message.reply_text("🔗 Your Channel Link:")
    return S_REG_CH

async def reg_ch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['r_ch'] = update.message.text
    await update.message.reply_text("✅ Total Deals Done?")
    return S_REG_DL

async def reg_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    report = f"💎 **SELLER REG**\nUser: {data['r_user']}\nChannel: {data['r_ch']}\nDeals: {update.message.text}"
    await context.bot.send_message(ADMIN_ID, report)
    await update.message.reply_text("✅ Sent to Admin!", reply_markup=main_menu())
    return ConversationHandler.END

# --- ADMIN: ADD SCAMMER ---
async def admin_add_scammer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    # Usage: /addscam @user Amount (Reply to proof photo)
    try:
        user = context.args[0].replace("@","")
        amt = context.args[1]
        fid = update.message.reply_to_message.photo[-1].file_id
        database.add_to_db("scammers", (user, amt, fid))
        await update.message.reply_text(f"🚫 {user} added to Scammer List!")
    except: await update.message.reply_text("Reply to proof with: /addscam @user Amount")

def main():
    database.init_db()
    threading.Thread(target=run_s, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(rep_init, pattern="^m_report$"),
            CallbackQueryHandler(check_init, pattern="^m_check$"),
            CallbackQueryHandler(reg_init, pattern="^m_reg$"),
        ],
        states={
            S_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_check)],
            S_REP_USR: [MessageHandler(filters.TEXT & ~filters.COMMAND, rep_usr)],
            S_REP_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, rep_amt)],
            S_REP_PRF: [MessageHandler(filters.PHOTO, rep_prf)],
            S_REG_USR: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_usr)],
            S_REG_CH: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_ch)],
            S_REG_DL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_dl)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addscam", admin_add_scammer))
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__': main()
