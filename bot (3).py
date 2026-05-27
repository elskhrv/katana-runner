import logging
import json
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://elskhrv.github.io/katana-runner")

scores = {}

ITEMS = {
    "life":     ("❤️ +1 жизнь",          "Продолжить игру",  50),
    "shield":   ("🛡 Щит",               "Защита от удара",  30),
    "slow":     ("⏳ Замедление",         "Скорость -50%",    40),
    "skin_red": ("🔴 Красный самурай",    "Скин навсегда",   150),
}


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    kb = [
        [InlineKeyboardButton("⚔️ Играть", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Рекорды", callback_data="top")],
    ]
    await update.message.reply_text(
        f"Привет, {name}! 🥷\n\n"
        "*Katana Runner* — самурайский раннер.\n"
        "Прыгай, соревнуйся с призраком друга!\n\n"
        "_Жизни можно купить за ⭐ Stars._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def shop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton(f"{t} — {s} ⭐", callback_data=f"buy_{k}")]
        for k, (t, _, s) in ITEMS.items()
    ]
    kb.append([InlineKeyboardButton("← Назад", callback_data="back")])
    await q.edit_message_text(
        "🛍 *Магазин*\nВыбери товар:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    item_id = q.data[4:]
    if item_id not in ITEMS:
        return
    title, desc, stars = ITEMS[item_id]
    await ctx.bot.send_invoice(
        chat_id=q.from_user.id,
        title=title,
        description=desc,
        payload=f"{item_id}:{q.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(title, stars)],
        provider_token="",
    )


async def precheckout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def paid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    item_id = update.message.successful_payment.invoice_payload.split(":")[0]
    title = ITEMS.get(item_id, (item_id,))[0]
    await update.message.reply_text(
        f"✅ Куплено: *{title}*\nОткрой игру чтобы применить!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⚔️ В игру", web_app=WebAppInfo(url=MINI_APP_URL))
        ]]),
    )


async def top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not scores:
        text = "🏆 *Рекорды*\n\nПока пусто — будь первым!"
    else:
        s = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        medals = ["🥇","🥈","🥉"]
        text = "🏆 *Топ игроков*\n\n" + "\n".join(
            f"{medals[i] if i<3 else str(i+1)+'.'} {sc} очков"
            for i, (_, sc) in enumerate(s)
        )
    await q.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("← Назад", callback_data="back")
        ]]),
    )


async def back(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [
        [InlineKeyboardButton("⚔️ Играть", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Рекорды", callback_data="top")],
    ]
    await q.edit_message_text(
        "⚔️ *Katana Runner*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(shop, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(top, pattern="^top$"))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, paid))
    logger.info("Бот запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
