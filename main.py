import os
import logging
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===== Tavily =====
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    logging.warning("Tavily not installed. Web search disabled.")
    TAVILY_AVAILABLE = False

# ================== ENV ==================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

logging.basicConfig(level=logging.INFO)

# ================== AI CLIENTS ==================
llm = InferenceClient(model="deepseek-ai/DeepSeek-V3.2-Exp", token=HF_TOKEN)

if TAVILY_AVAILABLE:
    tavily = TavilyClient(api_key=TAVILY_API_KEY)

# ================== MEMORY ==================
user_sessions = {}

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = (
    "You are Nexora, a private and intelligent Telegram AI assistant. "
    "You NEVER mention searching, browsing, tools, APIs, models, or external sources. "
    "If you have updated or real-world information, you present it naturally as existing knowledge."
)

# ================== HELPERS ==================
def needs_web_search(text: str) -> bool:
    keywords = [
        "latest", "today", "now", "current",
        "news", "price", "update", "recent",
        "who won", "score", "happening","time"
    ]
    return any(word in text.lower() for word in keywords)

def silent_web_search(query: str) -> str:
    if not TAVILY_AVAILABLE:
        return ""
    try:
        result = tavily.search(query=query, max_results=5, include_answer=True)
        return result.get("answer") or ""
    except Exception as e:
        logging.error(f"Tavily search failed: {e}")
        return ""

# ================== HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}\n\n"
        "🤖 *Nexora* is online.\nAsk me anything.",
        parse_mode="Markdown"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    await update.message.chat.send_action(ChatAction.TYPING)

    if user_id not in user_sessions:
        user_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # ---- Silent Web Context ----
    if TAVILY_AVAILABLE and needs_web_search(text):
        web_info = silent_web_search(text)
        if web_info:
            user_sessions[user_id].append({
                "role": "system",
                "content": f"Background knowledge for answering naturally:\n{web_info}"
            })

    user_sessions[user_id].append({"role": "user", "content": text})

    try:
        response = llm.chat_completion(
            messages=user_sessions[user_id],
            max_tokens=350,
            temperature=0.7
        )
        reply = response.choices[0].message["content"]
    except Exception as e:
        logging.error(e)
        reply = "⚠️ Something went wrong. Please try again."

    user_sessions[user_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

# ================== RUN BOT ==================
import asyncio

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("✅ Nexora is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())