"""AI Telegram bot: Gemini -> Groq -> OpenRouter navbat bilan."""

import logging
import os
from collections import defaultdict, deque

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from providers import AllProvidersFailed, ProviderPool, load_providers

load_dotenv()
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Sen foydali yordamchisan. Foydalanuvchi qaysi tilda yozsa, o'sha tilda qisqa va aniq javob ber.",
)
HISTORY_LEN = int(os.getenv("HISTORY_LEN", "10"))
TELEGRAM_LIMIT = 4096

pool = ProviderPool(load_providers())
# Har bir chat uchun oxirgi xabarlar (bot qayta ishga tushsa o'chadi)
history: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_LEN))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Salom! Savolingizni yozing.\n/new — suhbatni yangidan boshlash")


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history.pop(update.effective_chat.id, None)
    await update.message.reply_text("Suhbat tozalandi.")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    h = history[chat_id]
    h.append({"role": "user", "content": update.message.text})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *h]

    try:
        answer, provider = await pool.chat(messages)
    except AllProvidersFailed:
        h.pop()
        await update.message.reply_text("Hozir hamma AI xizmatlar band. Birozdan keyin qayta urinib ko'ring.")
        return

    log.info("chat %s: javob %s orqali", chat_id, provider)
    h.append({"role": "assistant", "content": answer})
    for i in range(0, len(answer), TELEGRAM_LIMIT):
        await update.message.reply_text(answer[i : i + TELEGRAM_LIMIT])


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN .env faylida yo'q")
    log.info("Faol xizmatlar: %s", ", ".join(p.name for p in pool.providers))

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.run_polling()


if __name__ == "__main__":
    main()
