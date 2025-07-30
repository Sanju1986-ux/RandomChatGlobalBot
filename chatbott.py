import os
import asyncio
from fastapi import FastAPI
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROUP_LINK = "https://t.me/randomchat_global"

# FastAPI app to keep Render Web Service alive
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot is running"}

# Telegram Bot setup
queue = []
active_chats = {}

keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🟢 Start Chat")],
        [KeyboardButton("🔄 Next"), KeyboardButton("❌ End Chat")]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Welcome {update.effective_user.first_name}!

"
        f"👉 Join our group if you'd like (optional):\n{GROUP_LINK}\n\n"
        "Then tap 🟢 Start Chat to meet a random stranger!",
        reply_markup=keyboard
    )

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        await update.message.reply_text("⚠️ You're already in a chat.")
        return

    if queue:
        partner_id = queue.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        await context.bot.send_message(partner_id, "🎉 Connected to a stranger! Say hi!")
        await update.message.reply_text("🎉 Connected to a stranger! Say hi!")
    else:
        queue.append(user_id)
        await update.message.reply_text("⏳ Waiting for a stranger to connect...")

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await end_chat(update, context)
    await start_chat(update, context)

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await context.bot.send_message(partner_id, "👋 Stranger left the chat.")
        await update.message.reply_text("✅ You left the chat.")
    elif user_id in queue:
        queue.remove(user_id)
        await update.message.reply_text("✅ You left the waiting queue.")
    else:
        await update.message.reply_text("⚠️ You are not in a chat.")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await context.bot.copy_message(chat_id=partner_id, from_chat_id=user_id, message_id=update.message.message_id)
    else:
        await update.message.reply_text("🟡 You're not in a chat. Press 🟢 Start Chat.")

# Function to start Telegram bot in background
async def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🟢 Start Chat$"), start_chat))
    app_bot.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🔄 Next$"), next_chat))
    app_bot.add_handler(MessageHandler(filters.TEXT & filters.Regex("^❌ End Chat$"), end_chat))
    app_bot.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))

    print("🤖 Bot is running...")
    await app_bot.run_polling()

# Start bot in background
asyncio.create_task(run_bot())
