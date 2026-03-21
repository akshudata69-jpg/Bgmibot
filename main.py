import os, threading, logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PORT = int(os.environ.get("PORT", 8080))

# --- STATES ---
CHECKING, REPORTING, BROADCASTING = range(3)

# --- WEB SERVER ---
server = Flask(__name__)
@server.route('/')
def h(): return "Bot Online", 200
def run_s(): server.run(host='0.0.0.0', port=PORT)

# --- KEYBOARDS ---
def get_main_menu():
    kbd = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="btn_check"), InlineKeyboardButton("🚨 Report Seller", callback_data="btn_report")],
        [InlineKeyboardButton("🏆 Top Sellers", callback_data="btn_top"), InlineKeyboardButton("🚫 Scammer List", callback_data="btn_scam")],
        [InlineKeyboardButton("🛒 Buy Accounts", url="https://t.me/AKSHARSTORE")]
    ]
    return InlineKeyboardMarkup(kbd)

def get_admin_menu():
    kbd = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_bc")],
        [InlineKeyboardButton("📊 Stats", callback_data="adm_stats")],
        [InlineKeyboardButton("⬅️ Back", callback_data="btn_start")]
    ]
    return InlineKeyboardMarkup(kbd)

# --- START & RESET ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.add_user(user.id, user.username) # Saves for broadcast
    context.user_data.clear() # CRITICAL: Clears all stuck states
    
    msg = "🛡️ **SafeDeal Marketplace System**\nUse the buttons below to verify sellers or report scams."
    
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=get_main_menu(), parse_mode='Markdown')
    else:
        await update.message.reply_text(msg, reply_markup=get_main_menu(), parse_mode='Markdown')
    return ConversationHandler.END

# --- ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("🛠 **Admin Control Panel**", reply_markup=get_admin_menu())

# --- BROADCAST SYSTEM ---
async def broadcast_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📢 Send the message you want to broadcast (Text only):")
    return BROADCASTING

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uids = database.get_all_users()
    count = 0
    for uid in uids:
        try:
            await context.bot.send_message(chat_id=uid, text=update.message.text)
            count += 1
        except: continue
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
    return ConversationHandler.END

# --- CHECK SELLER ---
async def check_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔍 Enter @username to check:")
    return CHECKING

async def do_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text.replace("@", "").strip()
    user = database.get_user_data(target)
    if not user:
        await update.message.reply_text("❓ Not found in database.")
    else:
        res = f"👤 @{user[1]}\n📊 Score: {user[4]}\n📢 Status: {user[6]}"
        await update.message.reply_text(res, reply_markup=get_main_menu())
    return ConversationHandler.END

# --- MAIN ENGINE ---
def main():
    database.init_db()
    threading.Thread(target=run_s, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    # The Logic: Entry Points reset the state every time a button is clicked
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(check_init, pattern="^btn_check$"),
            CallbackQueryHandler(broadcast_init, pattern="^adm_bc$"),
            CallbackQueryHandler(start, pattern="^btn_start$"),
        ],
        states={
            CHECKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_check)],
            BROADCASTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(start, pattern="^btn_start$")],
        allow_reentry=True # Allows clicking other buttons mid-flow
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel)) # Only you can use this
    app.add_handler(conv)
    
    print("Bot 100% Operational.")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
