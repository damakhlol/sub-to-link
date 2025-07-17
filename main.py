import re
import base64
import requests
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import NetworkError
from config import BOT_TOKEN

async def send_message(update: Update, text: str):
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except:
        pass

def fetch_subscription(url: str):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        content = response.text.strip()
        try:
            decoded = base64.b64decode(content).decode()
            return decoded.strip().splitlines()
        except:
            return content.strip().splitlines()
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(update, "سلام! لطفاً لینک اشتراک خود را ارسال کنید⚪️.")

async def ask_link_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str):
    keyboard = [[
        InlineKeyboardButton("🔗 تکی", callback_data="single"),
        InlineKeyboardButton("📜 همه با هم", callback_data="all")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗃حالت ارسال را انتخاب کنید:", reply_markup=reply_markup)
    context.user_data["subscription_link"] = link

async def process_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    link = context.user_data.get("subscription_link")
    if not link:
        await query.message.reply_text("لینک اشتراک پیدا نشد.")
        return

    links = fetch_subscription(link)
    if not links:
        await query.message.reply_text("کانفیگ‌ها دریافت نشدند.")
        return

    valid_links = [l for l in links if l.strip()]
    if not valid_links:
        await query.message.reply_text("هیچ کانفیگ معتبری یافت نشد.")
        return

    if query.data == "all":
        config_file = "config.txt"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("\n".join(valid_links))

        try:
            with open(config_file, "rb") as f:
                await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=f,
                    filename="config.txt",
                    caption=f"{len(valid_links)} کانفیگ استخراج شد ✅"
                )
        except Exception as e:
            print("خطا در ارسال فایل:", e)
            await context.bot.send_message(chat_id=query.from_user.id, text="خطا در ارسال فایل.")

        try:
            os.remove(config_file)
        except:
            pass

    elif query.data == "single":
        for link in valid_links:
            await query.message.reply_text(f"<code>{link}</code>", parse_mode=ParseMode.HTML)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if re.match(r'^http', text):
        await ask_link_mode(update, context, text)
    else:
        await send_message(update, "لطفاً فقط لینک اشتراک معتبر را ارسال کنید.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(process_links, pattern="^(single|all)$"))
    app.run_polling()

if __name__ == "__main__":
    main()
