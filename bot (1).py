"""
Katana Runner — Telegram Bot
"""
import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://elskhrv.github.io/katana-runner")

scores: dict[int, int] = {}

SHOP_ITEMS = {
    "life":     {"title": "❤️ +1 жизнь",             "description": "Продолжить игру с дополнительной жизнью", "stars": 50},
    "shield":   {"title": "🛡 Щит",                   "description": "Защита от одного удара",                  "stars": 30},
    "slow":     {"title": "⏳ Замедление",             "description": "Скорость -50% на 10 секунд",             "stars": 40},
    "skin_red": {"title": "🔴 Скин «Красный самурай»", "description": "Уникальный скин навсегда",               "stars": 150},
}


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("⚔️ Играть", web_app={"url": MINI_APP_URL})],
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Рекорды", callback_data="leaderboard")],
    ]
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🥷\n\n"
        "Добро пожаловать в *Katana Runner*!\n\n"
        "Прыгай через препятствия, соревнуйся с призраком друга!\n\n"
        "_Тап — прыжок. Жизни можно купить за Stars._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def shop_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
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
        "🛍 *Магазин Katana Runner*\n\nВыбери товар:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def buy_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.replace("buy_", "")
    item = SHOP_ITEMS.get(item_id)
    if not item:
        await query.answer("Товар не найден", show_alert=True)
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


async def precheckout(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    item_id, user_id = payload.split(":")
    item = SHOP_ITEMS.get(item_id)
    logger.info(f"Оплата: user={user_id}, item={item_id}")
    await update.message.reply_text(
        f"✅ Куплено: *{item['title']}*\n\nОткрой игру чтобы применить!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⚔️ В игру", web_app={"url": MINI_APP_URL})
        ]])
    )


async def leaderboard_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not scores:
        text = "🏆 *Таблица рекордов*\n\nПока никто не играл. Будь первым!"
    else:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, sc) in enumerate(sorted_scores):
            medal = medals[i] if i < 3 else f"{i+1}."
            lines.append(f"{medal} Игрок — {sc} очков")
        text = "🏆 *Топ игроков*\n\n" + "\n".join(lines)
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("← Назад", callback_data="back")
        ]])
    )


async def back_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("⚔️ Играть", web_app={"url": MINI_APP_URL})],
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Рекорды", callback_data="leaderboard")],
    ]
    await query.edit_message_text(
        "⚔️ *Katana Runner*\nВыбери действие:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def web_app_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    data = json.loads(update.message.web_app_data.data)
    user_id = update.effective_user.id
    new_score = data.get("score", 0)
    old_best = scores.get(user_id, 0)
    if new_score > old_best:
        scores[user_id] = new_score
        await update.message.reply_text(
            f"🏆 Новый рекорд: *{new_score}* очков!",
            parse_mode="Markdown"
        )


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(shop_handler, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(leaderboard_handler, pattern="^leaderboard$"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^back$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    logger.info("Бот запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
