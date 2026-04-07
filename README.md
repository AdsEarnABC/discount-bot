# 🤖 Discount Bot — Інструкція запуску

## Що тобі потрібно
- Комп'ютер або безкоштовний сервер (Railway)
- Python 3.11+ (безкоштовно)
- Telegram Bot Token (вже є ✅)

---

## 🚀 Варіант 1 — Запуск на Railway (БЕЗКОШТОВНО, рекомендую)

### Крок 1: Створи акаунт
Зайди на https://railway.app → Sign Up (через GitHub)

### Крок 2: Створи GitHub репозиторій
1. Зайди на https://github.com → New repository
2. Назви "discount-bot" → Create
3. Завантаж туди всі файли (bot.py, database.py, requirements.txt + цей README)

### Крок 3: Деплой на Railway
1. Railway → New Project → Deploy from GitHub repo
2. Обери свій "discount-bot" репозиторій
3. Settings → Variables → додай змінну:
   - `BOT_TOKEN` = `8230533382:AAFk_95WIrLh0uv9wzo1hfxVCX7bPN-UMVc`
   - `ADMIN_ID`  = (свій Telegram ID, дізнайся у @userinfobot)
4. Deploy! Бот запуститься автоматично 🎉

---

## 💻 Варіант 2 — Запуск локально на комп'ютері

### Крок 1: Встанови Python
Завантаж з https://python.org/downloads → встанови

### Крок 2: Розпакуй файли
Створи папку `discount_bot`, поклади туди всі файли

### Крок 3: Відкрий термінал в цій папці
Windows: Shift + ПКМ → "Відкрити вікно PowerShell тут"

### Крок 4: Встанови залежності
```
pip install -r requirements.txt
```

### Крок 5: Встав свій токен
Відкрий `bot.py` у блокноті, знайди рядок:
```python
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТУТ_ТВІЙ_ТОКЕН")
```
Токен вже вставлений ✅

### Крок 6: Запусти бота
```
python bot.py
```

Бот працює! Відкрий Telegram → знайди свого бота → /start

---

## 💰 Як заробляти

### 1. Партнерська програма Rozetka
- Зареєструйся: https://rozetka.com.ua/ua/affiliate/
- Отримай свій partner_id
- Заміни в bot.py: `PARTNER_TAG = "?utm_source=discountbot&aff_id=ТВІЙ_ID"`
- З кожної покупки через твоє посилання = до 5% комісії 💵

### 2. Преміум підписка (наступний крок)
- Додай оплату через LiqPay або Monobank API
- Безкоштовно: 3 категорії, 5 товарів у watchlist
- Преміум (99 грн/міс): всі категорії, 20 товарів, щогодинні знижки

### 3. Реклама магазинів
Коли набереш 500+ користувачів — магазини самі будуть писати 📩

---

## 📊 Адмін команди
- `/stats` — статистика користувачів (тільки для тебе)

Щоб увімкнути: у файлі bot.py знайди `ADMIN_ID = 0`
Заміни 0 на свій Telegram ID (дізнайся у @userinfobot)

---

## ❓ Питання?
Якщо щось не працює — повертайся до Claude, покажи помилку і виправимо!
