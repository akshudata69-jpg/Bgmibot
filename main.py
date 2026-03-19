import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from database import init_db, search_scammer, add_scammer
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

SEARCHING, ADDING_SCAM = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    keyboard = [[InlineKeyboardButton("🔍 Search ID", callback_data='search')]]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("➕ Add Scammer (Admin)", callback_data='admin_add')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛡️ **BGMI Anti-Scam Bot**\nSelect an option:", reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'search':
        await query.message.reply_text("🔍 Send the **BGMI ID** to check:")
        return SEARCHING
    elif query.data == 'admin_add':
        await query.message.reply_text("📝 Send details as: `ID - Reason - ProofLink`")
        return ADDING_SCAM

async def process_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = search_scammer(update.message.text)
    if res:
        await update.message.reply_text(f"❌ **SCAMMER!**\nID: {res[0]}\nReason: {res[1]}\nProof: {res[2]}")
    else:
        await update.message.reply_text("✅ No record found. Use a Middleman!")
    return ConversationHandler.END

async def process_admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return ConversationHandler.END
    try:
        parts = update.message.text.split(" - ")
        if add_scammer(parts[0], parts[1], parts[2]):
            await update.message.reply_text("✅ Added to Blacklist!")
        else:
            await update.message.reply_text("❌ Error adding ID.")
    except:
        await update.message.reply_text("❌ Format: ID - Reason - Link")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search)],
            ADDING_SCAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin_add)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    
    print("Bot is starting...")
    # This specific line fixes the 'AttributeError' on Render
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
