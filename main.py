import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from database import init_db
from dotenv import load_dotenv

# --- FAKE SERVER FOR RENDER ---
flask_app = Flask(__name__)
@flask_app.route('/')
def health_check():
    return "Bot is Running!", 200

def run_flask():
    # Render provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)
# ------------------------------

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

def main():
    init_db()
    
    # Start the "Fake" server in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Build the Telegram Bot
    app = Application.builder().token(TOKEN).build()
    
    # (Add your handlers here like before...)
    # app.add_handler(CommandHandler("start", start))
    
    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
