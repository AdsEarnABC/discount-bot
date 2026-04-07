import asyncio
import logging
import os
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import Database

# ── Налаштування ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8230533382:AAFk_95WIrLh0uv9wzo1hfxVCX7bPN-UMVc")
ADMIN_ID  = int(os.getenv("ADMIN_ID", "0"))   # Свій Telegram ID впиши сюди

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

db = Database("bot.db")

# ── Категорії ─────────────────────────────────────────────────
CATEGORIES = {
    "electronics": "📱 Електроніка",
    "appliances":  "🏠 Побутова техніка",
    "clothes":     "👗 Одяг та взуття",
    "sports":      "⚽ Спорт",
    "beauty":      "💄 Краса та здоров'я",
}

PARTNER_TAG = "?utm_source=discountbot&utm_medium=referral"

# ══════════════════════════════════════════════════════════════
#  СКРАПІНГ ЗНИЖОК З ROZETKA
# ══════════════════════════════════════════════════════════════
ROZETKA_CATS = {
    "electronics": "noutbuki-490370",
    "appliances":  "holodilniki-77974",
    "clothes":     "zhenskaya-odezhda-258618",
    "sports":      "sport-i-razvlecheniya-1306",
    "beauty":      "kosmetika-i-parfyumeriya-1503",
}

async def fetch_rozetka_deals(category: str) -> list[dict]:
    cat_slug = ROZETKA_CATS.get(category, "")
    if not cat_slug:
        return []
    url = (
        f"https://search.rozetka.com.ua/ua/search/api/v6/"
        f"?front-type=xl&country=UA&lang=ua&section_id={cat_slug.split('-')[-1]}"
        f"&sort=cheap&page=1"
    )
    deals = []
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return []
                data = await r.json()
                goods = data.get("data", {}).get("goods", [])
                for g in goods[:8]:
                    old = g.get("old_price") or 0
                    new = g.get("price") or 0
                    if old and new and old > new:
                        disc = round((1 - new / old) * 100)
                        if disc >= 20:
                            gid = g.get("id", "")
                            deals.append({
                                "title":     g.get("title", "Без назви")[:60],
                                "price":     new,
                                "old_price": old,
                                "discount":  disc,
                                "url":       f"https://rozetka.com.ua/ua/{gid}/p{gid}/{PARTNER_TAG}",
                                "store":     "🛍 Rozetka",
                            })
    except Exception as e:
        log.warning(f"Rozetka error ({category}): {e}")
    return deals


async def fetch_all_deals(categories: list[str]) -> list[dict]:
    results = await asyncio.gather(*[fetch_rozetka_deals(c) for c in categories])
    out = []
    for r in results:
        out.extend(r)
    out.sort(key=lambda x: x["discount"], reverse=True)
    return out

# ══════════════════════════════════════════════════════════════
#  КОМАНДИ
# ══════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.first_name, user.username or "")
    text = (
        f"👋 Привіт, *{user.first_name}*!\n\n"
        "Я знаходжу найкращі знижки в українських магазинах 🔥\n\n"
        "📱 Електроніка · 🏠 Техніка · 👗 Одяг · ⚽ Спорт · 💄 Краса\n\n"
        "Обери категорії які тебе цікавлять 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=_cats_kb(user.id))


async def cmd_deals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    cats = db.get_user_categories(uid)
    if not cats:
        await update.message.reply_text("⚠️ Спочатку обери категорії: /categories")
        return
    msg = await update.message.reply_text("🔍 Шукаю знижки...")
    deals = await fetch_all_deals(cats)
    if not deals:
        await msg.edit_text("😔 Наразі немає знижок ≥20%. Спробуй пізніше!")
        return
    await msg.edit_text(f"🔥 Знайшов *{len(deals)}* акцій для тебе!", parse_mode="Markdown")
    for d in deals[:5]:
        await _send_deal(update.effective_chat.id, d, ctx.bot)


async def cmd_categories(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        "📂 Обери категорії (✅ = обрано):",
        reply_markup=_cats_kb(uid)
    )


async def cmd_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    items = db.get_watchlist(uid)
    if not items:
        await update.message.reply_text(
            "📋 Watchlist порожній.\n\nПросто *надішли назву товару* — буду стежити за ціною!",
            parse_mode="Markdown"
        )
        return
    text = "📋 *Твій watchlist:*\n\n" + "\n".join(f"{i}. {it['name']}" for i, it in enumerate(items, 1))
    text += "\n\nНатисни ❌ щоб видалити товар:"
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=_watchlist_kb(items))


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    s = db.get_stats()
    await update.message.reply_text(
        f"📊 *Статистика*\n\n👤 Користувачів: {s['users']}\n🔔 Активних: {s['active']}\n📋 Watchlist: {s['watchlist']}",
        parse_mode="Markdown"
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Команди:*\n\n"
        "/start — головне меню\n"
        "/deals — знайти знижки зараз\n"
        "/categories — обрати категорії\n"
        "/watchlist — відстежувані товари\n\n"
        "💡 Надішли назву товару — додам до watchlist!",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════════════════════════
#  CALLBACK & MESSAGES
# ══════════════════════════════════════════════════════════════
async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    uid  = q.from_user.id
    data = q.data
    await q.answer()

    if data.startswith("cat:"):
        db.toggle_category(uid, data[4:])
        await q.edit_message_reply_markup(_cats_kb(uid))

    elif data.startswith("rm_watch:"):
        db.remove_from_watchlist(uid, int(data[9:]))
        items = db.get_watchlist(uid)
        if items:
            await q.edit_message_reply_markup(_watchlist_kb(items))
        else:
            await q.edit_message_text("📋 Watchlist тепер порожній!")

    elif data == "find_deals":
        await cmd_deals(update, ctx)


async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    text = update.message.text.strip()
    if len(text) < 3:
        return
    items = db.get_watchlist(uid)
    if len(items) >= 10:
        await update.message.reply_text("⚠️ Максимум 10 товарів. Видали старі: /watchlist")
        return
    db.add_to_watchlist(uid, text)
    await update.message.reply_text(
        f"✅ Додав *{text}* до watchlist!\nПовідомлю як знайду знижку 🔔",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════════════════════════
#  ПЛАНОВА РОЗСИЛКА
# ══════════════════════════════════════════════════════════════
async def broadcast(app: Application):
    log.info("⏰ Планова розсилка...")
    for user in db.get_active_users():
        try:
            cats  = db.get_user_categories(user["id"])
            if not cats:
                continue
            deals = await fetch_all_deals(cats)
            if not deals:
                continue
            await app.bot.send_message(user["id"],
                f"🔥 *{len(deals)} нових знижок для тебе!*", parse_mode="Markdown")
            for d in deals[:3]:
                await _send_deal(user["id"], d, app.bot)
        except Exception as e:
            log.warning(f"Broadcast fail {user['id']}: {e}")

# ══════════════════════════════════════════════════════════════
#  ДОПОМІЖНІ ФУНКЦІЇ
# ══════════════════════════════════════════════════════════════
def _cats_kb(uid: int) -> InlineKeyboardMarkup:
    sel = set(db.get_user_categories(uid))
    rows = []
    for key, label in CATEGORIES.items():
        mark = "✅" if key in sel else "⬜"
        rows.append([InlineKeyboardButton(f"{mark} {label}", callback_data=f"cat:{key}")])
    rows.append([InlineKeyboardButton("🔍 Знайти знижки!", callback_data="find_deals")])
    return InlineKeyboardMarkup(rows)


def _watchlist_kb(items: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"❌ {it['name'][:35]}", callback_data=f"rm_watch:{it['id']}")]
        for it in items
    ])


async def _send_deal(chat_id: int, deal: dict, bot):
    text = (
        f"{deal['store']}\n"
        f"*{deal['title']}*\n\n"
        f"💰 *{deal['price']} грн* ~~{deal['old_price']} грн~~\n"
        f"🏷 Знижка: *{deal['discount']}%*"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Купити", url=deal["url"])]])
    await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    db.init()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("deals",      cmd_deals))
    app.add_handler(CommandHandler("categories", cmd_categories))
    app.add_handler(CommandHandler("watchlist",  cmd_watchlist))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CommandHandler("help",       cmd_help))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(broadcast, "interval", hours=2, args=[app])
    scheduler.start()

    log.info("🤖 Бот запущено!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
