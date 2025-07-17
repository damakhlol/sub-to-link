import re
import base64
import requests
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, InlineQueryHandler
from telegram.error import NetworkError, BadRequest
from config import BOT_TOKEN

async def send_message(update: Update, text: str):
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except NetworkError as e:
        print(f"خطای شبکه در ارسال پیام: {e}")
        await asyncio.sleep(5)
        try:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"خطا در ارسال پیام پس از تلاش مجدد: {e}")

def fetch_subscription(url: str):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        content = response.text.strip()
        try:
            if base64.b64encode(base64.b64decode(content)).decode() == content:
                decoded = base64.b64decode(content).decode()
                return decoded.strip().split("\n")
        except:
            return content.strip().split("\n")
    except requests.RequestException as e:
        print(f"خطا در دریافت اشتراک: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message(update, "سلام 👋\nلطفاً لینک اشتراک خود را ارسال کنید 🌐")

async def ask_link_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str):
    keyboard = [[
        InlineKeyboardButton("🔗 تکی", callback_data="single"),
        InlineKeyboardButton("📜 همه با هم", callback_data="all")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠️ حالت ارسال لینک‌ها را انتخاب کنید:", reply_markup=reply_markup)
    context.user_data["subscription_link"] = link

async def process_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass

    link = context.user_data.get("subscription_link")
    if not link:
        await query.message.reply_text("❌ خطا: لینک اشتراک یافت نشد! 😔")
        return

    links = fetch_subscription(link)
    if not links or not any(link.strip() for link in links):
        await query.message.reply_text("❌ دریافت لینک‌ها با خطا مواجه شد یا اشتراک معتبر نیست 😔")
        return

    valid_links = [l for l in links if l.strip()]
    if not valid_links:
        await query.message.reply_text("✅ هیچ لینک معتبری یافت نشد. شاید اشتراک از نوع دیگری باشد 🌐")
        return

    config_file = "configs.txt"
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_links))

    if query.data == "single":
        for link in valid_links:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={requests.utils.quote(link)}"
            msg = f"<b>لینک اتصال:</b>\n<code>{link}</code>"
            await query.message.reply_text(msg, parse_mode=ParseMode.HTML)
            await query.message.reply_photo(qr_url, caption="🔗 QR کد لینک")
            await query.message.reply_text("━━━━━━━━━━━━━━")
    elif query.data == "all":
        try:
            with open(config_file, "rb") as f:
                await query.message.reply_document(document=f, filename="configs.txt", caption="📄 همه کانفیگ‌ها داخل این فایل هستند ✅")
        except Exception as e:
            await query.message.reply_text(f"❌ خطا در ارسال فایل: {str(e)}")

    try:
        os.remove(config_file)
    except:
        pass

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query or not re.match(r'^http', query):
        return

    context.user_data["inline_subscription_link"] = query

    results = [
        InlineQueryResultArticle(
            id="1",
            title="کانفیگ‌ها دریافت شد، جهت ارسال روی این دکمه کلیک کنید",
            input_message_content=InputTextMessageContent("کانفیگ‌ها دریافت شد، جهت ارسال روی این دکمه کلیک کنید"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📥 ارسال کانفیگ‌ها", callback_data="inline_send")
            ]])
        )
    ]
    try:
        await update.inline_query.answer(results)
    except BadRequest as e:
        print(f"خطای BadRequest در inline_query: {e}")
        await update.inline_query.answer([])
    except NetworkError as e:
        print(f"خطای شبکه در inline_query: {e}")
        await asyncio.sleep(5)
        try:
            await update.inline_query.answer(results)
        except Exception as e:
            print(f"خطا در پاسخ به inline query پس از تلاش مجدد: {e}")

async def inline_process_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id if query.message else query.from_user.id
    link = context.user_data.get("inline_subscription_link")
    if not link:
        await context.bot.send_message(chat_id=chat_id, text="❌ خطا: لینک اشتراک یافت نشد! 😔")
        return

    links = fetch_subscription(link)
    if not links or not any(link.strip() for link in links):
        await context.bot.send_message(chat_id=chat_id, text="❌ دریافت لینک‌ها با خطا مواجه شد یا اشتراک معتبر نیست 😔")
        return

    valid_links = [l for l in links if l.strip()]
    if not valid_links:
        await context.bot.send_message(chat_id=chat_id, text="✅ هیچ لینک معتبری یافت نشد. شاید اشتراک از نوع دیگری باشد 🌐")
        return

    config_file = "configs.txt"
    with open(config_file, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_links))

    try:
        with open(config_file, "rb") as f:
            if query.message:
                await query.message.reply_document(document=f, filename="configs.txt")
            else:
                await context.bot.send_document(chat_id=chat_id, document=f, filename="configs.txt")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ خطا در ارسال فایل: {str(e)}")

    try:
        os.remove(config_file)
    except:
        pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if re.match(r'^http', text):
        await ask_link_mode(update, context, text)
    elif not text.startswith('/'):
        await send_message(update, "❗️ لطفاً فقط لینک اشتراک معتبر را ارسال کنید 🌐")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(process_links, pattern="^(single|all)$"))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(inline_process_links, pattern="^inline_send$"))
    app.run_polling()

if __name__ == "__main__":
    main()
