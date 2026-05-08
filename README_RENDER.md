# Renderga joylash uchun qo'llanma

## 1. GitHubga yuklash
```
git init
git add .
git commit -m "AdMarket Coin bot"
git branch -M main
git remote add origin https://github.com/username/AdMarket_Coin.git
git push -u origin main
```

## 2. Render.com sozlamalari
1. Render.com ga kirib "New Web Service" tanlang
2. GitHub repositoryni ulang
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. Environment Variables qo'shing:
   - `API_TOKEN`: 8444256532:AAGmpavcAWq_hR0mBhh_KOxf6CVJlq_UkM4
   - `WEB_APP_URL`: https://sizning-app-namingiz.onrender.com
   - `MONGO_URL`: mongodb+srv://javlonbekqadamov11111_db_user:javlonbekqadamov11111_db_user@cluster0.4pjg413.mongodb.net/?appName=Cluster0

## 3. Web App URL ni yangilang
Bot ishga tushgandan so'ng, .env fayl va bot.py dagi WEB_APP_URL ni o'z app URLingiz bilan almashtiring.
