# AdMarket Coin Bot

Bu Telegram bot AdMarket Coin uchun, MongoDB bilan foydalanuvchilarni saqlaydi.

## O'rnatish

1. Python 3.8+ o'rnating.
2. Kutubxonalarni o'rnating: `pip install -r requirements.txt`
3. MongoDB URL ni bot.py da o'zgartiring.
4. Telegram bot tokenini o'zgartiring.

## Ishga tushirish

Mahalliy: `python bot.py`

## Renderda Deploy

1. Kodni GitHub ga push qiling.
2. Render.com da yangi Web Service yarating.
3. GitHub repo ni ulang.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`
6. Environment Variables:
   - `RENDER_EXTERNAL_URL`: Sizning Render app URL (masalan, https://your-app.onrender.com)
   - Agar kerak, `PORT`: 10000 (default)

Bot webhook orqali ishlaydi, va index.html ni serv qiladi.

## Xavfsizlik

- HTTPS ishlatiladi.
- MongoDB URL ni himoya qiling.
- Bot tokenini sir saqlang.