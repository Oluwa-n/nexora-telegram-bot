import os
import logging
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import nest_asyncio

# Apply nest_asyncio to allow async loops in Railway
nest_asyncio.apply()

# === LOAD ENV VARIABLES ===
load_dotenv()  # only needed if you use .env locally

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not TELEGRAM_TOKEN or not HF_TOKEN:
    raise ValueError("Please set TELEGRAM_TOKEN and HF_TOKEN in env variables!")

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === HUGGING FACE CLIENT ===
client = InferenceClient("deepseek-ai/DeepSeek-V3.2-Exp", token=HF_TOKEN)

# === PER-USER SESSION STORAGE ===
user_sessions = {}

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 DeepSeek AI is online! Type anything to chat.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    # Show typing indicator
    await update.message.chat.send_action(action="typing")

    # Initialize session if first message
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {
                "role": "system",
                "content": (
                    "You are a personal assistant for your creator. "
                    "Follow the creator instructions carefully. "
                    "You can respond freely and help with advice, coding, and other tasks. "
                    "Always ask questions if needed, and adapt to user's style."
                )
            }
        ]

    # Add user message to session
    user_sessions[user_id].append({"role": "user", "content": user_input})

    # Generate AI response from Hugging Face DeepSeek
    response = client.chat_completion(
        model="deepseek-ai/DeepSeek-V3.2-Exp",
        messages=user_sessions[user_id],
        max_tokens=250,
        temperature=0.7,
    )

    ai_reply = response.choices[0].message["content"]

    # Send AI response
    await update.message.reply_text(ai_reply)

    # Add assistant response to session
    user_sessions[user_id].append({"role": "assistant", "content": ai_reply})

# === RUN TELEGRAM BOT ===
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("✅ Nexora Telegram Bot is running...")

# Run bot
app.run_polling()
