import os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# CONFIG
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
# STATES
SEARCH, REPORT_ID, REPORT_REASON, REPORT_PROOF, BROADCAST_MSG, REG_SELLER = range(6)

# --- WEB SERVER FOR RENDER ---
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot Active", 200
def run_flask(): app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_user(update.effective_user.id) # Capture ID for Broadcast
    keyboard = [
        [InlineKeyboardButton("🔍 Check ID/Seller", callback_data='search')],
        [InlineKeyboardButton("🚩 Report Scammer", callback_data='report')],
        [InlineKeyboardButton("💎 Top Sellers (Trusted)", callback_data='top_sellers')],
        [InlineKeyboardButton("🤝 Middleman Service", callback_data='middleman')],
        [InlineKeyboardButton("📝 Register as Seller", callback_data='reg_seller')]
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ ADMIN PANEL", callback_data='admin_panel')])
    
    await update.message.reply_text("🛡️ **BGMI Anti-Scam Central**\nSafe trading starts here.", 
                                   reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID: return
    
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data='admin_bc')],
        [InlineKeyboardButton("📥 Pending Approvals", callback_data='admin_approve')],
        [InlineKeyboardButton("➕ Add Top Seller", callback_data='admin_add_seller')]
    ]
    await query.message.edit_text("🔧 **Admin Control Center**", reply_markup=InlineKeyboardMarkup(keyboard))

# --- BROADCAST SYSTEM ---
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📣 Send the message (text) you want to broadcast to ALL users:")
    return BROADCAST_MSG

async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = database.get_all_users()
    msg = update.message.text
    count = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=user, text=f"📢 **ANNOUNCEMENT**\n\n{msg}", parse_mode='Markdown')
            count += 1
        except: continue
    await update.message.reply_text(f"✅ Sent to {count} users.")
    return ConversationHandler.END

# --- MIDDLEMAN SECTION ---
async def middleman_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤝 **Verified Middleman Service**\n"
        "To avoid scams, always use an admin as a middleman.\n\n"
        "1. @YourUsername (Owner)\n2. @Helper1\n3. @Helper2\n\n"
        "**Fee:** 10% of deal value.\nClick below to request a deal."
    )
    btn = [[InlineKeyboardButton("📩 Request Middleman", url=f"https://t.me/akshudata69")]]
    await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode='Markdown')

# --- TOP SELLERS (THE REVENUE) ---
async def top_sellers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text(
        "💎 **100% Trusted Top Sellers**\n"
        "To view the list of verified UC & Account sellers, a one-time fee of **₹50** is required to ensure serious buyers only.\n\n"
        "Contact @akshudata69 to get access."
    )

# --- (Add other handlers for Report, Approve, Search similarly) ---

def main():
    database.init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    # Conversations
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_broadcast, pattern='^admin_bc$'),
            # Add other entry points
        ],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT, do_broadcast)],
            # Add other states
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    app.add_handler(CallbackQueryHandler(middleman_info, pattern='^middleman$'))
    app.add_handler(CallbackQueryHandler(top_sellers, pattern='^top_sellers$'))
    
    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
