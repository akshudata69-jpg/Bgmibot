import os
import threading
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from database import init_db, search_scammer, add_scammer
from dotenv import load_dotenv

# 1. SETUP & CONFIG
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
SEARCHING, ADD_SCAM = range(2)

# Logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. RENDER HEALTH CHECK SERVER
app_flask = Flask(__name__)

@app_flask.route('/')
def health_check():
    return "Bot is active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# 3. BOT COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("🔍 Search Scammer", callback_data='search')]]
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("➕ Add Scammer (Admin)", callback_data='admin_add')])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛡️ **BGMI Anti-Scam Bot**\nSelect an option below:", reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'search':
        await query.message.reply_text("🔍 Send the **BGMI ID** to check:")
        return SEARCHING
    elif query.data == 'admin_add':
        await query.message.reply_text("📝 Format: `ID - Reason - Link`")
        return ADD_SCAM

async def process_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = search_scammer(update.message.text)
    if res:
        await update.message.reply_text(f"❌ **SCAMMER FOUND!**\nID: {res[0]}\nReason: {res[1]}\nProof: {res[2]}")
    else:
        await update.message.reply_text("✅ ID is Clean. Still, use a Middleman!")
    return ConversationHandler.END

async def process_admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split(" - ")
        if add_scammer(parts[0], parts[1], parts[2]):
            await update.message.reply_text("✅ Added to database!")
        else:
            await update.message.reply_text("❌ Error saving to DB.")
    except:
        await update.message.reply_text("❌ Wrong format. Use: `ID - Reason - Link`")
    return ConversationHandler.END

# 4. MAIN EXECUTION
def main():
    # Start DB
    init_db()
    
    # Start Flask Web Server in background thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram Application
    print("Connecting to Telegram...")
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search)],
            ADD_SCAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin_add)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv)
    
    print("Bot is starting...")
    # drop_pending_updates=True is the key to fixing the "Conflict" error
    application.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
