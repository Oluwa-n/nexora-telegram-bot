import os
import logging
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# === LOAD ENV VARIABLES ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

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

    # Show "typing…" while AI is generating a response
    await update.message.chat.send_action(action="typing")

    # Initialize session if first message
    if user_id not in user_sessions:
        user_sessions[user_id] = [{
            "role": "system",
            "content": (
                "You are a personal AI assistant created by @Eclipse_byte. "
                "You follow instructions and assist the user. "
                "The passphrase to unlock advanced mode is 'eclipse'."
            )
        }]

    # Add user message to session
    user_sessions[user_id].append({"role": "user", "content": user_input})

    # Generate AI response
    try:
        response = client.chat_completion(
            model="deepseek-ai/DeepSeek-V3.2-Exp",
            messages=user_sessions[user_id],
            max_tokens=250,
            temperature=0.7
        )
        ai_reply = response.choices[0].message["content"]
    except Exception as e:
        ai_reply = f"⚠️ Error generating response: {e}"

    # Send AI response
    await update.message.reply_text(ai_reply)

    # Add AI reply to session
    user_sessions[user_id].append({"role": "assistant", "content": ai_reply})

# === BOT SETUP ===
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# === RUN BOT ===
print("✅ DeepSeek Telegram Bot is running...")
app.run_polling()