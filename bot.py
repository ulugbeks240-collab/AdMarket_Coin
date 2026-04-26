import sqlite3
import json
import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- SOZLAMALAR ---
API_TOKEN = '8444256532:AAGmpavcAWq_hR0mBhh_KOxf6CVJlq_UkM4'
WEB_APP_URL = "https://husinbayxudayberganov8807-hub.github.io/AdMarket_Uz/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect('admarket.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 100, 
                       yum_balance REAL DEFAULT 0.0, yum_wallet TEXT, 
                       staking_amount REAL DEFAULT 0.0, mining_power INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, 
                       channel_link TEXT, remaining_subs INTEGER, 
                       price_type TEXT DEFAULT 'diamond', price_amount INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS completed_tasks 
                      (user_id, task_id TEXT, reward_type TEXT DEFAULT 'diamond', 
                       reward_amount INTEGER DEFAULT 10, PRIMARY KEY (user_id, task_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS yum_transactions 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                       transaction_type TEXT, amount REAL, description TEXT, 
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS mining_rewards 
                      (user_id INTEGER, last_mining DATETIME, 
                       daily_mining REAL DEFAULT 0.0, PRIMARY KEY (user_id))''')
    conn.commit()
    conn.close()

# --- ASOSIY START KOMANDASI ---
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    # message.get_args() ni xavfsiz olish (Aiogram 2.x uslubi)
    args = message.get_args()

    conn = sqlite3.connect('admarket.db')
    cursor = conn.cursor()

    # 1. Foydalanuvchini ro'yxatga olish va Referral tizimi
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        # Yangi userga 30 diamond + 50 YUM bonus
        cursor.execute("INSERT INTO users (user_id, balance, yum_balance) VALUES (?, ?, ?)", (user_id, 30, 50.0))
        
        # Taklif qilgan odamga +80
        if args and args.isdigit() and int(args) != user_id:
            referrer_id = int(args)
            cursor.execute("UPDATE users SET balance = balance + 80, yum_balance = yum_balance + 20 WHERE user_id = ?", (referrer_id,))
            try:
                await bot.send_message(referrer_id, "🎉 **Do'stingiz qo'shildi!**\nSizga +80 💎 + 20 🪙 Coin bonus berildi.")
            except: pass
        conn.commit()

    # 2. Ma'lumotlarni yig'ish
    cursor.execute("SELECT balance, yum_balance, yum_wallet FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    user_balance = user_data[0]
    yum_balance = user_data[1]
    yum_wallet = user_data[2] or "Not set"
    
    cursor.execute("SELECT channel_link, remaining_subs FROM ads WHERE owner_id = ?", (user_id,))
    my_ads = cursor.fetchall()
    
    cursor.execute("SELECT id, channel_link FROM ads WHERE owner_id != ?", (user_id,))
    active_tasks = cursor.fetchall() 
    conn.close()

    # 3. UI yuborish (Vizual qism)
    photo_url = "https://i.postimg.cc/RVDdbP5b/6ee3a319-1706-4d24-8b16-86212c853a63.png"
    
    caption = (
        f"👋 **Assalomu alaykum, {message.from_user.first_name}!**\n\n"
        f"🤑 **AdMarket Coin** — kripto reklama bozori\n"
        f"Vazifalarni bajarib 💎 va 🪙 ishlang!\n\n"
        f"💰 **Diamond balans:** `{user_balance}` 💎\n"
        f"🪙 **Coin balans:** `{yum_balance:.2f}` 🪙\n"
        f"📈 **Faol topshiriqlar:** {len(active_tasks)} ta\n"
        f"💳 **Coin Wallet:** `{yum_wallet}`\n\n"
        f"🚀 Boshlash uchun pastdagi tugmani bosing:"
    )

    markup = InlineKeyboardMarkup(row_width=2)
    
    # Ma'lumotlarni JSON qilib WebApp'ga yuborish
    my_ads_data = json.dumps(my_ads)
    tasks_data = json.dumps(active_tasks)
    web_app_url_full = f"{WEB_APP_URL}?v={user_id}&bal={user_balance}&yum={yum_balance}&wallet={yum_wallet}&my_ads={my_ads_data}&tasks={tasks_data}"
    
    # Tugmalar
    btn_start = InlineKeyboardButton("🚀 ADMARKET COIN", web_app=WebAppInfo(url=web_app_url_full))
    btn_guide = InlineKeyboardButton("📖 Qo'llanma", callback_data="guide")
    btn_ref = InlineKeyboardButton("👥 Do'stlarni taklif qilish", switch_inline_query=f"{user_id}")
    
    markup.add(btn_start) # Asosiy tugma katta (row_width=1 kabi)
    markup.row(btn_guide, btn_ref) # Ikkita kichik tugma yonma-yon

    try:
        await message.answer_photo(
            photo=photo_url, 
            caption=caption, 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
    except Exception as e:
        # Agar rasm yuklanmasa, matnning o'zini yuboradi
        await message.answer(caption, reply_markup=markup, parse_mode="Markdown")

# --- WEB APP DAN KELGAN MA'LUMOTLARNI QABUL QILISH ---
@dp.message_handler(content_types=['web_app_data'])
async def get_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        user_id = message.from_user.id
        conn = sqlite3.connect('admarket.db')
        cursor = conn.cursor()

        if data.get('action') == "check_task":
            task_id = data.get('task_id')
            reward_type = data.get('reward_type', 'diamond')
            cursor.execute("SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
            if cursor.fetchone():
                await message.answer("❌ Bu vazifani bajargansiz!")
            else:
                cursor.execute("UPDATE ads SET remaining_subs = remaining_subs - 1 WHERE id = ?", (task_id,))
                
                if reward_type == 'yum':
                    cursor.execute("UPDATE users SET yum_balance = yum_balance + 5 WHERE user_id = ?", (user_id,))
                    cursor.execute("INSERT INTO completed_tasks (user_id, task_id, reward_type, reward_amount) VALUES (?, ?, ?, ?)", (user_id, task_id, 'yum', 5))
                    await message.answer("✅ Vazifa bajarildi! +5 🪙")
                else:
                    cursor.execute("UPDATE users SET balance = balance + 10 WHERE user_id = ?", (user_id,))
                    cursor.execute("INSERT INTO completed_tasks (user_id, task_id, reward_type, reward_amount) VALUES (?, ?, ?, ?)", (user_id, task_id, 'diamond', 10))
                    await message.answer("✅ Vazifa bajarildi! +10 💎")
                conn.commit()

        elif data.get('action') == "create_task":
            cost = int(data.get('cost', 0))
            link = data.get('channel', '')
            amount = int(data.get('amount', 0))
            price_type = data.get('price_type', 'diamond')
            
            if price_type == 'yum':
                cursor.execute("SELECT yum_balance FROM users WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()
                if user_data and user_data[0] >= cost:
                    cursor.execute("UPDATE users SET yum_balance = yum_balance - ? WHERE user_id = ?", (cost, user_id))
                    cursor.execute("INSERT INTO ads (owner_id, channel_link, remaining_subs, price_type, price_amount) VALUES (?, ?, ?, ?, ?)", 
                                   (user_id, link, amount, 'yum', cost))
                    conn.commit()
                    await message.answer(f"✅ Reklama qabul qilindi!\nKanal: {link}\nTo'lov: {cost} 🪙 Coin")
                else:
                    await message.answer("❌ Coiningiz yetarli emas!")
            else:
                cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()
                if user_data and user_data[0] >= cost:
                    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (cost, user_id))
                    cursor.execute("INSERT INTO ads (owner_id, channel_link, remaining_subs, price_type, price_amount) VALUES (?, ?, ?, ?, ?)", 
                                   (user_id, link, amount, 'diamond', cost))
                    conn.commit()
                    await message.answer(f"✅ Reklama qabul qilindi!\nKanal: {link}\nTo'lov: {cost} 💎")
                else:
                    await message.answer("❌ Olmosingiz yetarli emas!")
        
        conn.close()
    except Exception as e:
        await message.answer(f"⚠️ Xatolik: {e}")

# --- YUM COIN WALLET FUNKSIYALARI ---
@dp.message_handler(commands=['wallet'])
async def wallet_command(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('admarket.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT yum_wallet FROM users WHERE user_id = ?", (user_id,))
    wallet = cursor.fetchone()[0]
    
    if wallet:
        await message.answer(f"💳 **Sizning Coin walletingiz:**\n`{wallet}`", parse_mode="Markdown")
    else:
        await message.answer("❌ Wallet ulanmagan. Wallet ulash uchun /setwallet komandasini yuboring.")
    
    conn.close()

@dp.message_handler(commands=['setwallet'])
async def set_wallet_command(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()
    
    if not args:
        await message.answer("📝 **Foydalanish:**\n`/setwallet <wallet_address>`\n\nMasalan: `/setwallet 0x1234...abcd`", parse_mode="Markdown")
        return
    
    conn = sqlite3.connect('admarket.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET yum_wallet = ? WHERE user_id = ?", (args, user_id))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ **Coin wallet muvaffaqiyatli ulandi!**\n\n📍 **Wallet manzili:**\n`{args}`", parse_mode="Markdown")

@dp.message_handler(commands=['withdraw'])
async def withdraw_command(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('admarket.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT yum_balance, yum_wallet FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        await message.answer("❌ Xatolik! Iltimos, qayta urinib ko'ring.")
        return
    
    yum_balance = result[0]
    yum_wallet = result[1]
    
    if not yum_wallet:
        await message.answer("❌ Avval wallet ulashingiz kerak! /setwallet komandasidan foydalaning.")
        return
    
    if yum_balance < 50:
        await message.answer("❌ Minimal chiqarish miqdori 50 🪙 Coin!")
        return
    
    # Chiqarish so'rovini yuborish (admin tasdiqisiz)
    cursor.execute("INSERT INTO yum_transactions (user_id, transaction_type, amount, description) VALUES (?, ?, ?, ?)", 
                   (user_id, 'withdraw', yum_balance, f'Wallet: {yum_wallet}'))
    conn.commit()
    conn.close()
    
    await message.answer(f"📤 **Chiqarish so'rovi yuborildi!**\n\n💰 **Miqdor:** `{yum_balance:.2f}` 🪙\n💳 **Wallet:** `{yum_wallet}`\n\n⏰ So'rov ko'rib chiqilmoqda...", parse_mode="Markdown")

@dp.callback_query_handler(text="guide")
async def guide_handler(call: types.CallbackQuery):
    await call.answer("Qo'llanma: Vazifalar bajarib  va  ishlang, wallet ulang, pul chiqaring, staking qiling!", show_alert=True)

if __name__ == '__main__':
    init_db()
    print("Bot muvaffaqiyatli ishga tushdi (Obunasiz rejim)!")
    executor.start_polling(dp, skip_updates=True)