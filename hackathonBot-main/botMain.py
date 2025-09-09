import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ChatAction
from openai import OpenAI

# Load API keys from .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI()

# Store test sessions
user_sessions = {}

# RIASEC test questions (2 per category for MVP)
riasec_questions = [
    ("Realistic", "Do you enjoy working with tools, machines, or being outdoors?"),
    ("Realistic", "Would you rather build something than sit in an office?"),
    ("Investigative", "Do you like solving puzzles or analyzing problems?"),
    ("Investigative", "Are you curious about how things work?"),
    ("Artistic", "Do you enjoy creative activities like writing, music, or drawing?"),
    ("Artistic", "Would you prefer an unstructured, expressive environment over a routine job?"),
    ("Social", "Do you like helping people or teaching others?"),
    ("Social", "Do you enjoy being part of a team or community effort?"),
    ("Enterprising", "Do you enjoy leading, persuading, or selling ideas?"),
    ("Enterprising", "Do you like taking initiative in group settings?"),
    ("Conventional", "Do you enjoy organizing data, records, or financial information?"),
    ("Conventional", "Do you prefer structure and clear rules in your work environment?")
]

# Motivation Anchors test questions (1 per anchor)
motivation_questions = [
    ("Autonomy", "Do you value being independent and having control over your own work?"),
    ("Security", "Do you prefer stable, long-term employment with predictable growth?"),
    ("Technical", "Do you like being an expert and going deep in a specific field?"),
    ("General Management", "Do you enjoy leading teams and having organizational influence?"),
    ("Lifestyle", "Do you want a job that gives you enough time for your personal life?"),
    ("Service", "Is helping others the most important part of a job for you?"),
    ("Creativity", "Do you feel fulfilled when creating something new or original?"),
    ("Challenge", "Do you seek out difficult problems to solve for the satisfaction of overcoming them?")
]

# Ask GPT with memory for chat mode
async def ask_gpt_conversational(history: list) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are a thoughtful career assistant AI."
                    " Ask several clarifying questions before making any career suggestions."
                    " Your goal is to understand the user well before giving advice."
                )}
            ] + history
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = {"mode": "choice"}
    await update.message.reply_text(
        "👋 Hi! I'm your career assistant bot.\n"
        "Choose how you'd like to begin:\n"
        "1️⃣ Type *chat* to talk freely about your career.\n"
        "2️⃣ Type *riasec* to take a short personality-based test.\n"
        "3️⃣ Type *motivation* to explore your core career motivators.\n",
        parse_mode="Markdown"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Init session if not exists
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"mode": "choice"}

    session = user_sessions[chat_id]

    # Handle mode selection
    if session["mode"] == "choice":
        if text.lower() == "chat":
            session["mode"] = "chat"
            session["history"] = []
            await update.message.reply_text("🧠 Okay, let's talk! Tell me about your background, goals, or ask a career question.")
            return
        elif text.lower() == "riasec":
            session["mode"] = "riasec"
            session["index"] = 0
            session["scores"] = {}
            await update.message.reply_text(riasec_questions[0][1])
            return
        elif text.lower() == "motivation":
            session["mode"] = "motivation"
            session["index"] = 0
            session["scores"] = {}
            await update.message.reply_text(motivation_questions[0][1])
            return
        else:
            await update.message.reply_text("❗Please type one of: *chat*, *riasec*, or *motivation*.", parse_mode="Markdown")
            return

    # Free chat mode with thoughtful flow
    elif session["mode"] == "chat":
        history = session.get("history", [])
        history.append({"role": "user", "content": text})
        session["history"] = history[-10:]  # Keep last 10 entries max
        response = await ask_gpt_conversational(session["history"])
        session["history"].append({"role": "assistant", "content": response})
        await update.message.reply_text(response)
        return

    # RIASEC test logic
    elif session["mode"] == "riasec":
        if text.lower() in ["yes", "no"]:
            category, _ = riasec_questions[session["index"]]
            if text.lower() == "yes":
                session["scores"][category] = session["scores"].get(category, 0) + 1
            session["index"] += 1
            if session["index"] < len(riasec_questions):
                await update.message.reply_text(riasec_questions[session["index"]][1])
            else:
                top = sorted(session["scores"].items(), key=lambda x: -x[1])[:2]
                result = ", ".join([f"{k}" for k, v in top])
                session["mode"] = "choice"
                await update.message.reply_text(f"✅ Test complete! Your top personality types: *{result}*", parse_mode="Markdown")
                await update.message.reply_text("Type *chat*, *riasec*, or *motivation* to continue.", parse_mode="Markdown")
        else:
            await update.message.reply_text("Please answer with 'yes' or 'no'.")
        return

    # Motivation test logic
    elif session["mode"] == "motivation":
        if text.lower() in ["yes", "no"]:
            category, _ = motivation_questions[session["index"]]
            if text.lower() == "yes":
                session["scores"][category] = session["scores"].get(category, 0) + 1
            session["index"] += 1
            if session["index"] < len(motivation_questions):
                await update.message.reply_text(motivation_questions[session["index"]][1])
            else:
                top = sorted(session["scores"].items(), key=lambda x: -x[1])[:2]
                result = ", ".join([f"{k}" for k, v in top])
                session["mode"] = "choice"
                await update.message.reply_text(f"✅ Test complete! Your top motivators: *{result}*", parse_mode="Markdown")
                await update.message.reply_text("Type *chat*, *riasec*, or *motivation* to continue.", parse_mode="Markdown")
        else:
            await update.message.reply_text("Please answer with 'yes' or 'no'.")
        return

# Setup bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🤖 Career Assistant Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
