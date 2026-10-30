import os, asyncio
from collections import defaultdict, deque
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          MessageHandler, filters, ContextTypes)
from rag import answer

load_dotenv(override=True)
history = defaultdict(lambda: deque(maxlen=6))

WELCOME = ("Halo! Saya asisten Customer Service TokoTeknoku. "
           "Tanyakan seputar garansi, return, spesifikasi produk, atau promo ya.")


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)


async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    h = history[uid]
    try:
        reply, escalate = await asyncio.to_thread(answer, text, list(h))
    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text(
            "Maaf, sistem sedang bermasalah. Silakan coba lagi sebentar lagi.")
        return

    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

    if escalate:
        # TODO: kirim notifikasi ke agen CS (email/Slack/grup Telegram)
        print(f"[ESKALASI] user={uid}: {text}")


async def non_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Maaf, saat ini saya hanya bisa membaca pesan teks ya.")


def main():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, non_text))
    print("Bot berjalan... (Ctrl+C untuk berhenti)")
    app.run_polling()


if __name__ == "__main__":
    main()