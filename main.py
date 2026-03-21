import os, threading, asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = "@AKSHARSTORE"

# --- STATES ---
ST_CHECK, ST_BROADCAST = range(2)

# --- WEB SERVER ---
server = Flask(__name__)
@server.route('/')
def h(): return "Bot Online", 200
def run_s(): server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- KEYBOARDS ---
def main_menu():
    kbd = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="btn_check"), InlineKeyboardButton("🚨 Report Seller", callback_data="btn_report")],
        [InlineKeyboardButton("🏆 Trusted Sellers", callback_data="btn_top"), InlineKeyboardButton("🚫 Scammer List", callback_data="btn_scam")],
        [InlineKeyboardButton("🛒 Buy Accounts", url="https://t.me/AKSHARSTORE")]
    ]
    return InlineKeyboardMarkup(kbd)

def admin_menu():
    kbd = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_bc")],
        [InlineKeyboardButton("📊 Total Users", callback_data="adm_stats")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="btn_start")]
    ]
    return InlineKeyboardMarkup(kbd)

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.add_user(user.id, user.username)
    
    msg = "🔥 **SafeDeal System Active**\nCheck reputations and trade securely."
    await (update.callback_query.message.edit_text if update.callback_query else update.message.reply_text)(
        msg, reply_markup=main_menu(), parse_mode='Markdown'
    )
    return ConversationHandler.END

# --- ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🛠 **Admin Control Panel**", reply_markup=admin_menu())

# --- BROADCAST LOGIC ---
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📢 Send the message you want to broadcast to ALL users:")
    return ST_BROADCAST

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = database.get_all_users()
    count = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=update.message.text)
            count += 1
        except: continue
    await update.message.reply_text(f"✅ Broadcast complete. Sent to {count} users.")
    return ConversationHandler.END

# --- CHECK SELLER ---
async def check_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔍 Send @username to check:")
    return ST_CHECK

async def do_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = database.get_user_data(update.message.text)
    if not user:
        await update.message.reply_text("❓ Not found in database.")
    else:
        res = f"👤 @{user[1]}\n📊 Score: {user[4]}\n📢 Status: {user[6]}"
        await update.message.reply_text(res, reply_markup=main_menu())
    return ConversationHandler.END

# --- MAIN ENGINE ---
def main():
    database.init_db()
    threading.Thread(target=run_s, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(check_init, pattern="^btn_check$"),
            CallbackQueryHandler(start_broadcast, pattern="^adm_bc$"),
        ],
        states={
            ST_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_check)],
            ST_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(start, pattern="^btn_start$"))
    app.add_handler(conv)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
