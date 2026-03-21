import os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import database

# --- SETTINGS ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# --- WEB SERVER ---
server = Flask(__name__)
@server.route('/')
def h(): return "Bot Live", 200
def run_s(): server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- MENU ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Check Seller", callback_data="ask_check"), InlineKeyboardButton("🚨 Report Seller", callback_data="ask_report")],
        [InlineKeyboardButton("📝 Register as Seller", callback_data="ask_reg")],
        [InlineKeyboardButton("🛒 Buy Accounts", url="https://t.me/AKSHARSTORE")]
    ])

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_user(update.effective_user.id)
    context.user_data.clear()
    msg = "🛡️ **SafeDeal Marketplace**\nProtect your trades from scammers."
    if update.callback_query: await update.callback_query.message.edit_text(msg, reply_markup=main_menu(), parse_mode='Markdown')
    else: await update.message.reply_text(msg, reply_markup=main_menu(), parse_mode='Markdown')

# --- BUTTON ROUTER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = query.data # Sets what the bot is waiting for

    if query.data == "ask_check":
        await query.message.reply_text("🔍 Send the **@username** you want to check:")
    elif query.data == "ask_report":
        await query.message.reply_text("🚨 Step 1: Send the Scammer's **@username**:")
    elif query.data == "ask_reg":
        await query.message.reply_text("📝 Step 1: Send your **Channel Link**:")

# --- TEXT & PHOTO HANDLER ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    text = update.message.text

    # 🔍 CHECK SELLER LOGIC
    if action == "ask_check":
        scam, sell = database.check_db(text)
        if scam:
            await update.message.reply_text(f"❌ **SCAMMER DETECTED!**\nUsername: @{scam[0]}\nAmount: {scam[1]}")
            await context.bot.send_photo(update.effective_chat.id, scam[2], caption="📄 **SCAM PROOF**")
        elif sell:
            await update.message.reply_text(f"✅ **VERIFIED SELLER**\nUsername: @{sell[0]}\nDeals: {sell[2]}\nChannel: {sell[1]}")
        else:
            await update.message.reply_text("❓ Not found. Trade with caution.", reply_markup=main_menu())
        context.user_data.clear()

    # 🚨 REPORT LOGIC (Multi-step)
    elif action == "ask_report":
        context.user_data['scam_user'] = text
        context.user_data['action'] = "ask_amount"
        await update.message.reply_text("💰 How much was the scam amount?")
    elif action == "ask_amount":
        context.user_data['scam_amt'] = text
        context.user_data['action'] = "ask_proof"
        await update.message.reply_text("📸 Send **Photo Proof** (Screenshot):")
    elif action == "ask_proof" and update.message.photo:
        fid = update.message.photo[-1].file_id
        await context.bot.send_photo(ADMIN_ID, fid, caption=f"🚨 **NEW REPORT**\nTarget: {context.user_data['scam_user']}\nAmount: {context.user_data['scam_amt']}\nBy: @{update.effective_user.username}")
        await update.message.reply_text("✅ Report forwarded to Admin!", reply_markup=main_menu())
        context.user_data.clear()

    # 📝 REGISTRATION LOGIC
    elif action == "ask_reg":
        context.user_data['reg_chan'] = text
        context.user_data['action'] = "ask_deals"
        await update.message.reply_text("✅ How many deals have you completed?")
    elif action == "ask_deals":
        msg = f"💎 **SELLER REGISTRATION**\nUser: @{update.effective_user.username}\nChannel: {context.user_data['reg_chan']}\nDeals: {text}"
        await context.bot.send_message(ADMIN_ID, msg)
        await update.message.reply_text("✅ Registration details sent to Admin!", reply_markup=main_menu())
        context.user_data.clear()

# --- ADMIN COMMANDS ---
async def add_scammer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user = context.args[0].replace("@","")
        amt = context.args[1]
        fid = update.message.reply_to_message.photo[-1].file_id
        database.add_to_db_scam(user, amt, fid) # Custom function needed or manual SQL
        await update.message.reply_text(f"🚫 @{user} added as Scammer.")
    except: await update.message.reply_text("Reply to proof photo with: /addscam @user Amount")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    users = database.get_all_users()
    for u in users:
        try: await context.bot.send_message(u, msg)
        except: continue
    await update.message.reply_text("📢 Broadcast sent!")

def main():
    database.init_db()
    threading.Thread(target=run_s, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("addscam", add_scammer))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, message_handler))
    
    app.run_polling()

if __name__ == '__main__': main()
