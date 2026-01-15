import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

# === ENV VARIABLES ===
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
    await update.message.reply_text("🤖 Nexora AI is online! Type anything to chat.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    await update.message.chat.send_action(action="typing")

    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "You are a personal assistant for your creator."}
        ]

    user_sessions[user_id].append({"role": "user", "content": user_input})

    response = client.chat_completion(
        model="deepseek-ai/DeepSeek-V3.2-Exp",
        messages=user_sessions[user_id],
        max_tokens=250,
        temperature=0.7,
    )

    ai_reply = response.choices[0].message["content"]
    await update.message.reply_text(ai_reply)
    user_sessions[user_id].append({"role": "assistant", "content": ai_reply})

# === BUILD APP ===
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
print("Nexora telgram bot is online")
app.run_polling()