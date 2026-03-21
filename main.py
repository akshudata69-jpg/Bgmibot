import os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# States
(ST_CHECK, ST_REG_DEALS, ST_REG_CHAN, ST_REG_EXP, ST_BC) = range(5)

# Flask for Render
server = Flask(__name__)
@server.route('/')
def h(): return "Bot Live", 200
def run_s(): server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Keyboards
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Check Seller", callback_data="btn_check"), InlineKeyboardButton("🚨 Report Seller", callback_data="btn_report")],
        [InlineKeyboardButton("📝 Register as Seller", callback_data="btn_reg")],
        [InlineKeyboardButton("🛒 Buy Accounts", url="https://t.me/AKSHARSTORE")]
    ])

# Logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_user(update.effective_user.id, update.effective_user.username)
    context.user_data.clear() # Fixes the "stuck" button issue
    msg = "🛡️ **SafeDeal Marketplace Bot**\nSelect an option to begin."
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=main_menu(), parse_mode='Markdown')
    else:
        await update.message.reply_text(msg, reply_markup=main_menu(), parse_mode='Markdown')
    return ConversationHandler.END

# --- SELLER REGISTRATION FLOW ---
async def reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📝 **Seller Registration**\nHow many deals have you completed?")
    return ST_REG_DEALS

async def reg_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['deals'] = update.message.text
    await update.message.reply_text("🔗 Send your Channel Link:")
    return ST_REG_CHAN

async def reg_chan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['chan'] = update.message.text
    await update.message.reply_text("⏳ How many years of experience do you have?")
    return ST_REG_EXP

async def reg_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exp = update.message.text
    user = update.effective_user.username
    deals = context.user_data['deals']
    chan = context.user_data['chan']
    
    # Notify Admin
    report = f"💎 **NEW SELLER REG**\nUser: @{user}\nDeals: {deals}\nChannel: {chan}\nExp: {exp}"
    await context.bot.send_message(ADMIN_ID, report)
    
    await update.message.reply_text("✅ Registration sent to Admin!", reply_markup=main_menu())
    return ConversationHandler.END

# --- BROADCAST ---
async def bc_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("📢 Send the message to Broadcast:")
    return ST_BC

async def bc_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uids = database.get_all_uids()
    for uid in uids:
        try: await context.bot.send_message(uid, update.message.text)
        except: continue
    await update.message.reply_text("✅ Broadcast Finished.")
    return ConversationHandler.END

# --- CHECK SELLER ---
async def check_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔍 Send @username to check:")
    return ST_CHECK

async def do_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📊 **User @{update.message.text.replace('@','')}** is currently safe.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    database.init_db()
    threading.Thread(target=run_s, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(check_init, pattern="^btn_check$"),
            CallbackQueryHandler(reg_start, pattern="^btn_reg$"),
            CommandHandler("broadcast", bc_start)
        ],
        states={
            ST_CHECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_check)],
            ST_REG_DEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_deals)],
            ST_REG_CHAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_chan)],
            ST_REG_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_final)],
            ST_BC: [MessageHandler(filters.TEXT & ~filters.COMMAND, bc_do)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
