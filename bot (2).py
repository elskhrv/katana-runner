"""
Katana Runner — Telegram Bot
"""
import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://elskhrv.github.io/katana-runner")

scores = {}

SHOP_ITEMS = {
    "life":     {"title": "❤️ +1 жизнь",             "description": "Продолжить игру", "stars": 50},
    "shield":   {"title": "🛡 Щит",                   "description": "Защита от удара", "stars": 30},
    "slow":     {"title": "⏳ Замедление",             "description": "Скорость -50%",  "stars": 40},
    "skin_red": {"title": "🔴 Красный самурай",        "description": "Скин навсегда",  "stars": 150},
}


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("⚔️ Играть", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Рекорды", callback_data="leaderboard")],
    ]
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🥷\n\n"
        "*Katana Runner* — самурайский раннер с призраком друга.\n\n"
        "_Тап — прыжок. Жизни покупаются за Stars._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def shop_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    buttons = []
    for item_id, item in SHOP_ITEMS.items():
        buttons.append([InlineKeyboardButton(
            f"{item['title']} — {item['stars']} ⭐",
            callback_data=f"buy_{item_id}"
        )])
    buttons.append([InlineKeyboardButton("← Назад", callback_data="back")])
    await query.edit_message_text(
        "🛍 *Магазин*\n\nВыбери товар:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def buy_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = query.data.replace("buy_", "")
    item = SHOP_ITEMS.get(item_id)
    if not item:
        return
    await ctx.bot.send_invoice(
        chat_id=query.from_user.id,
        title=item["title"],
        description=item["description"],
        payload=f"{item_id}:{query.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(item["title"], item["stars"])],
        provider_token="",
    )


async def precheckout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    item_id = payment.invoice_payload.split(":")[0]
    item = SHOP_ITEMS.get(item_id, {})
    await update.message.reply_text(
        f"✅ Куплено: *{item.get('title', item_id)}*\n\nОткрой игру чтобы применить!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⚔️ В игру", web_app=WebAppInfo(url=MINI_APP_URL))
        ]])
    )


async def leaderboard_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not scores:
        text = "🏆 *Рекорды*\n\nПока никто не играл. Будь первым!"
    else:
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = [f"{medals[i] if i < 3 else str(i+1)+'.'} Игрок — {sc}" for i, (_, sc) in enumerate(top)]
        text = "🏆 *Топ игроков*\n\n" + "\n".join(lines)
    await query.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="back")]])
    )


async def back_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("⚔️ Играть", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Рекорды", callback_data="leaderboard")],
    ]
    await query.edit_message_text(
        "⚔️ *Katana Runner*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(shop_handler, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(leaderboard_handler, pattern="^leaderboard$"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^back$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    logger.info("Бот запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
