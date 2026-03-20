import os, threading, logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = "@AKSHARSTORE"
PORT = int(os.environ.get("PORT", 8080))

# --- STATES ---
CHECK, R_USER, R_REASON, R_PROOF, REG_DATA = range(5)

# --- WEB SERVER ---
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot Running", 200
def run_flask(): app_flask.run(host='0.0.0.0', port=PORT)

# --- FORCE JOIN CHECK ---
async def is_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=update.effective_user.id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- MAIN MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_member(update, context):
        kbd = [[InlineKeyboardButton("Join @AKSHARSTORE", url=f"https://t.me/{CHANNEL_ID[1:]}")],
               [InlineKeyboardButton("✅ I Joined, Check Again", callback_data="start")]]
        await update.message.reply_text("❌ **Access Denied!**\nYou must join our channel to use this bot.", reply_markup=InlineKeyboardMarkup(kbd))
        return

    kbd = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="check"), InlineKeyboardButton("🚨 Report Seller", callback_data="report")],
        [InlineKeyboardButton("🏆 Top Sellers", callback_data="top"), InlineKeyboardButton("🚫 Scammer List", callback_data="scammers")],
        [InlineKeyboardButton("📝 Register as Seller", callback_data="register")],
        [InlineKeyboardButton("🛒 Buy Accounts From Us", url="https://t.me/AKSHARSTORE")]
    ]
    await update.message.reply_text(f"🛡️ **Welcome to BGMI Trust Bot**\nVerified by {CHANNEL_ID}", reply_markup=InlineKeyboardMarkup(kbd))

# --- CHECK SELLER LOGIC ---
async def check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🔍 Send the @username of the seller:")
    return CHECK

async def do_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.replace("@", "")
    user = database.get_user(username)
    
    if not user:
        await update.message.reply_text("❓ **User not found.**\nThey haven't been registered or reported yet.")
    else:
        # User index: 0:id, 1:username, 2:reports, 3:vouches, 4:score, 5:verified, 7:status
        badge = "👑 VERIFIED" if user[5] else "👤 Standard"
        text = (f"👤 **User:** @{user[1]}\n"
                f"🏷️ **Badge:** {badge}\n"
                f"📊 **Trust Score:** {user[4]}\n"
                f"✅ **Vouches:** {user[3]} | 🚩 **Reports:** {user[2]}\n"
                f"📢 **Status:** {user[7]}")
        await update.message.reply_text(text)
    return ConversationHandler.END

# --- REPORT SYSTEM (WITH PROOF) ---
async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🚨 Who are you reporting? Send @username:")
    return R_USER

async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target'] = update.message.text
    await update.message.reply_text("📝 What is the reason? (Scam, Fake, etc.)")
    return R_REASON

async def report_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reason'] = update.message.text
    await update.message.reply_text("📸 Send a Screenshot as proof (Photo):")
    return R_PROOF

async def report_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id
    target = context.user_data['target']
    
    # Send to Admin for Approval
    kbd = [[InlineKeyboardButton("✅ Approve (+5 Vouch)", callback_data=f"apprv_v_{target}"),
            InlineKeyboardButton("❌ Reject", callback_data="rej")]]
    
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, 
                               caption=f"📥 **New Report**\nFrom: {update.effective_user.username}\nTarget: {target}\nReason: {context.user_data['reason']}",
                               reply_markup=InlineKeyboardMarkup(kbd))
    
    await update.message.reply_text("✅ Report sent to Admin for review.")
    return ConversationHandler.END

# --- ADMIN BUTTON HANDLERS ---
async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("apprv_v_"):
        target = data.replace("apprv_v_", "")
        database.update_score(target, v_mod=1) # Increment vouch
        await query.message.edit_caption("✅ Report Approved! Vouch added to seller.")

# --- MAIN ---
def main():
    database.init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    # Conv Handlers
    check_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_start, pattern="^check$")],
        states={CHECK: [MessageHandler(filters.TEXT, do_check)]},
        fallbacks=[CommandHandler('start', start)]
    )
    
    report_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(report_start, pattern="^report$")],
        states={
            R_USER: [MessageHandler(filters.TEXT, report_user)],
            R_REASON: [MessageHandler(filters.TEXT, report_reason)],
            R_PROOF: [MessageHandler(filters.PHOTO, report_proof)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(check_conv)
    app.add_handler(report_conv)
    app.add_handler(CallbackQueryHandler(handle_approval, pattern="^apprv_"))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$")) # Force join retry

    print("Bot is 100% Live...")
    app.run_polling()

if __name__ == '__main__':
    main()
