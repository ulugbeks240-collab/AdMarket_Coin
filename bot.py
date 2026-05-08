import json
import datetime
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pymongo import MongoClient
from bson import ObjectId
from flask import Flask, send_from_directory
from dotenv import load_dotenv

# --- SOZLAMALAR ---
load_dotenv()

API_TOKEN = os.environ.get('API_TOKEN', '8444256532:AAGmpavcAWq_hR0mBhh_KOxf6CVJlq_UkM4')
WEB_APP_URL = os.environ.get('WEB_APP_URL', "https://your-app-name.onrender.com")  # Render URL ni shu yerga qo'ying

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', "mongodb+srv://javlonbekqadamov11111_db_user:javlonbekqadamov11111_db_user@cluster0.4pjg413.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URL)
db = client['admarket_db']

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Flask app for serving index.html
app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# --- MA'LUMOTLAR BAZASI ---
# MongoDB is schemaless, no init needed

# --- ASOSIY START KOMANDASI ---
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    # message.get_args() ni xavfsiz olish (Aiogram 2.x uslubi)
    args = message.get_args()

    # 1. Foydalanuvchini ro'yxatga olish va Referral tizimi
    user = db.users.find_one({"user_id": user_id})
    if user is None:
        # Yangi userga 30 diamond + 50 YUM bonus
        db.users.insert_one({
            "user_id": user_id,
            "balance": 30,
            "yum_balance": 50.0,
            "yum_wallet": None,
            "staking_amount": 0.0,
            "mining_power": 1
        })
        
        # Taklif qilgan odamga +80
        if args and args.isdigit() and int(args) != user_id:
            referrer_id = int(args)
            db.users.update_one({"user_id": referrer_id}, {"$inc": {"balance": 80, "yum_balance": 20}})
            try:
                await bot.send_message(referrer_id, "🎉 **Do'stingiz qo'shildi!**\nSizga +80 💎 + 20 🪙 Coin bonus berildi.")
            except: pass

    # 2. Ma'lumotlarni yig'ish
    user = db.users.find_one({"user_id": user_id})
    user_balance = user.get("balance", 0)
    yum_balance = user.get("yum_balance", 0.0)
    yum_wallet = user.get("yum_wallet", "Not set")
    
    my_ads_cursor = db.ads.find({"owner_id": user_id})
    my_ads = [{"id": str(ad["_id"]), "channel_link": ad["channel_link"], "remaining_subs": ad["remaining_subs"]} for ad in my_ads_cursor]
    
    active_tasks_cursor = db.ads.find({"owner_id": {"$ne": user_id}})
    active_tasks = [{"id": str(ad["_id"]), "channel_link": ad["channel_link"]} for ad in active_tasks_cursor]

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

        if data.get('action') == "check_task":
            task_id = data.get('task_id')
            reward_type = data.get('reward_type', 'diamond')
            if db.completed_tasks.find_one({"user_id": user_id, "task_id": task_id}):
                await message.answer("❌ Bu vazifani bajargansiz!")
            else:
                db.ads.update_one({"_id": ObjectId(task_id)}, {"$inc": {"remaining_subs": -1}})
                
                if reward_type == 'yum':
                    db.users.update_one({"user_id": user_id}, {"$inc": {"yum_balance": 5}})
                    db.completed_tasks.insert_one({"user_id": user_id, "task_id": task_id, "reward_type": 'yum', "reward_amount": 5})
                    await message.answer("✅ Vazifa bajarildi! +5 🪙")
                else:
                    db.users.update_one({"user_id": user_id}, {"$inc": {"balance": 10}})
                    db.completed_tasks.insert_one({"user_id": user_id, "task_id": task_id, "reward_type": 'diamond', "reward_amount": 10})
                    await message.answer("✅ Vazifa bajarildi! +10 💎")

        elif data.get('action') == "create_task":
            cost = int(data.get('cost', 0))
            link = data.get('channel', '')
            amount = int(data.get('amount', 0))
            price_type = data.get('price_type', 'diamond')
            
            if price_type == 'yum':
                user = db.users.find_one({"user_id": user_id})
                if user and user.get('yum_balance', 0) >= cost:
                    db.users.update_one({"user_id": user_id}, {"$inc": {"yum_balance": -cost}})
                    db.ads.insert_one({
                        "owner_id": user_id,
                        "channel_link": link,
                        "remaining_subs": amount,
                        "price_type": 'yum',
                        "price_amount": cost
                    })
                    await message.answer(f"✅ Reklama qabul qilindi!\nKanal: {link}\nTo'lov: {cost} 🪙 Coin")
                else:
                    await message.answer("❌ Coiningiz yetarli emas!")
            else:
                user = db.users.find_one({"user_id": user_id})
                if user and user.get('balance', 0) >= cost:
                    db.users.update_one({"user_id": user_id}, {"$inc": {"balance": -cost}})
                    db.ads.insert_one({
                        "owner_id": user_id,
                        "channel_link": link,
                        "remaining_subs": amount,
                        "price_type": 'diamond',
                        "price_amount": cost
                    })
                    await message.answer(f"✅ Reklama qabul qilindi!\nKanal: {link}\nTo'lov: {cost} 💎")
                else:
                    await message.answer("❌ Olmosingiz yetarli emas!")
        
    except Exception as e:
        await message.answer(f"⚠️ Xatolik: {e}")

# --- YUM COIN WALLET FUNKSIYALARI ---
@dp.message_handler(commands=['wallet'])
async def wallet_command(message: types.Message):
    user_id = message.from_user.id
    
    user = db.users.find_one({"user_id": user_id})
    wallet = user.get('yum_wallet') if user else None
    
    if wallet:
        await message.answer(f"💳 **Sizning Coin walletingiz:**\n`{wallet}`", parse_mode="Markdown")
    else:
        await message.answer("❌ Wallet ulanmagan. Wallet ulash uchun /setwallet komandasini yuboring.")
    

@dp.message_handler(commands=['setwallet'])
async def set_wallet_command(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()
    
    if not args:
        await message.answer("📝 **Foydalanish:**\n`/setwallet <wallet_address>`\n\nMasalan: `/setwallet 0x1234...abcd`", parse_mode="Markdown")
        return
    
    db.users.update_one({"user_id": user_id}, {"$set": {"yum_wallet": args}})
    
    await message.answer(f"✅ **Coin wallet muvaffaqiyatli ulandi!**\n\n📍 **Wallet manzili:**\n`{args}`", parse_mode="Markdown")

@dp.message_handler(commands=['withdraw'])
async def withdraw_command(message: types.Message):
    user_id = message.from_user.id
    
    user = db.users.find_one({"user_id": user_id})
    
    if not user:
        await message.answer("❌ Xatolik! Iltimos, qayta urinib ko'ring.")
        return
    
    yum_balance = user.get('yum_balance', 0)
    yum_wallet = user.get('yum_wallet')
    
    if not yum_wallet:
        await message.answer("❌ Avval wallet ulashingiz kerak! /setwallet komandasidan foydalaning.")
        return
    
    if yum_balance < 50:
        await message.answer("❌ Minimal chiqarish miqdori 50 🪙 Coin!")
        return
    
    # Chiqarish so'rovini yuborish (admin tasdiqisiz)
    db.yum_transactions.insert_one({
        "user_id": user_id,
        "transaction_type": 'withdraw',
        "amount": yum_balance,
        "description": f'Wallet: {yum_wallet}',
        "timestamp": datetime.datetime.now()
    })
    
    await message.answer(f"📤 **Chiqarish so'rovi yuborildi!**\n\n💰 **Miqdor:** `{yum_balance:.2f}` 🪙\n💳 **Wallet:** `{yum_wallet}`\n\n⏰ So'rov ko'rib chiqilmoqda...", parse_mode="Markdown")

@dp.callback_query_handler(text="guide")
async def guide_handler(call: types.CallbackQuery):
    await call.answer("Qo'llanma: Vazifalar bajarib  va  ishlang, wallet ulang, pul chiqaring, staking qiling!", show_alert=True)

if __name__ == '__main__':
    print("Bot muvaffaqiyatli ishga tushdi (Obunasiz rejim)!")
    executor.start_polling(dp, skip_updates=True)