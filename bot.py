import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import requests
import json
import sqlite3
from datetime import datetime
import time
import re

BOT_TOKEN = "8954981282:AAFPuBkSQCqXfMWCtUyFfDIsVp0HhlarZLw"
WEB_URL = "http://127.0.0.1:5000"
ADMIN_ID = "6040186314"
GROUP_ID = "-1004318807187"

bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

# ============ БАЗА ДАННЫХ БОТА ============
DB_NAME = 'velosher_bot.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            phone TEXT,
            location TEXT,
            location_lat TEXT,
            location_lng TEXT,
            language TEXT DEFAULT 'ru',
            total_orders INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ БД бота создана")

def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'telegram_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'phone': user[3],
            'location': user[4],
            'location_lat': user[5],
            'location_lng': user[6],
            'language': user[7],
            'total_orders': user[8]
        }
    return None

def save_user(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (telegram_id, username, first_name, phone, location, location_lat, location_lng, language, total_orders, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('telegram_id'),
        data.get('username', ''),
        data.get('first_name', ''),
        data.get('phone', ''),
        data.get('location', ''),
        data.get('location_lat', ''),
        data.get('location_lng', ''),
        data.get('language', 'ru'),
        data.get('total_orders', 0),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    return True

def update_language(telegram_id, lang):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (lang, telegram_id))
    conn.commit()
    conn.close()

def send_user_to_web(telegram_id):
    """Отправить пользователя на веб-сайт"""
    try:
        user = get_user(telegram_id)
        if not user:
            return
        url = f"{WEB_URL}/api/user/save_from_bot"
        data = {
            'telegram_id': user['telegram_id'],
            'username': user.get('username', ''),
            'first_name': user.get('first_name', ''),
            'phone': user.get('phone', ''),
            'address': user.get('location', ''),
            'location': user.get('location', ''),
            'location_lat': user.get('location_lat', ''),
            'location_lng': user.get('location_lng', ''),
            'language': user.get('language', 'ru')
        }
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            print(f"✅ Пользователь {telegram_id} отправлен на сайт")
        else:
            print(f"⚠️ Ошибка отправки: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка отправки пользователя: {e}")

init_db()

# ============ ПЕРЕВОДЫ ============
T = {
    'ru': {
        'menu': "🏠 *Главное меню*\n\nВыберите действие:",
        'catalog': "🛍️ Каталог",
        'cart': "🛒 Корзина",
        'profile': "👤 Мой профиль",
        'orders': "📋 Мои заказы",
        'lang_btn': "🌐 Сменить язык",
        'help': "ℹ️ Помощь",
        'start_reg': "👋 *Добро пожаловать!*\n\nДля оформления заказа заполните профиль:",
        'ask_location': "📍 *Шаг 1/3: Отправьте локацию*\nНажмите кнопку ниже:",
        'location_ok': "✅ *Локация получена!*\n\n📝 *Шаг 2/3: Ваше имя*\nВведите ваше имя:",
        'name_ok': "✅ *Имя сохранено!*\n\n📱 *Шаг 3/3: Ваш телефон*\nОтправьте номер:",
        'profile_ok': "✅ *Профиль готов!* 🎉\n\n👤 Имя: {name}\n📱 Телефон: {phone}\n📍 Адрес: {address}\n\nТеперь можно делать заказы!",
        'cancel': "❌ Отменено",
        'help_text': "ℹ️ *Помощь*\n\n🔐 Админ-панель: {admin_url}",
        'no_orders': "📋 У вас пока нет заказов",
        'no_location': "📍 Локация не найдена",
        'location_link': "📍 [Открыть на карте]({link})",
        'lang_ru': "🇷🇺 Русский",
        'lang_uz': "🇺🇿 O'zbekcha",
        'choose_lang': "🌐 *Выберите язык:*",
        'profile_info': "👤 *Ваш профиль*\n\n🆔 ID: {id}\n👤 Имя: {name}\n📱 Телефон: {phone}\n📍 Адрес: {address}\n📦 Заказов: {orders}\n🌐 Язык: {lang}",
        'back': "🔙 Назад"
    },
    'uz': {
        'menu': "🏠 *Bosh menyu*\n\nTanlang:",
        'catalog': "🛍️ Katalog",
        'cart': "🛒 Savat",
        'profile': "👤 Mening profilim",
        'orders': "📋 Mening buyurtmalarim",
        'lang_btn': "🌐 Tilni o'zgartirish",
        'help': "ℹ️ Yordam",
        'start_reg': "👋 *Xush kelibsiz!*\n\nBuyurtma berish uchun profilingizni to'ldiring:",
        'ask_location': "📍 *1/3 qadam: Joylashuvni yuboring*\nPastdagi tugmani bosing:",
        'location_ok': "✅ *Joylashuv qabul qilindi!*\n\n📝 *2/3 qadam: Ismingiz*\nIsmingizni kiriting:",
        'name_ok': "✅ *Ism saqlandi!*\n\n📱 *3/3 qadam: Telefoningiz*\nRaqamingizni yuboring:",
        'profile_ok': "✅ *Profil tayyor!* 🎉\n\n👤 Ism: {name}\n📱 Telefon: {phone}\n📍 Manzil: {address}\n\nEndi buyurtma berishingiz mumkin!",
        'cancel': "❌ Bekor qilindi",
        'help_text': "ℹ️ *Yordam*\n\n🔐 Admin panel: {admin_url}",
        'no_orders': "📋 Sizda hali buyurtmalar yo'q",
        'no_location': "📍 Joylashuv topilmadi",
        'location_link': "📍 [Xaritada ochish]({link})",
        'lang_ru': "🇷🇺 Ruscha",
        'lang_uz': "🇺🇿 O'zbekcha",
        'choose_lang': "🌐 *Tilni tanlang:*",
        'profile_info': "👤 *Profilingiz*\n\n🆔 ID: {id}\n👤 Ism: {name}\n📱 Telefon: {phone}\n📍 Manzil: {address}\n📦 Buyurtmalar: {orders}\n🌐 Til: {lang}",
        'back': "🔙 Orqaga"
    }
}

def get_lang(telegram_id):
    user = get_user(telegram_id)
    if user:
        return user.get('language', 'ru')
    return 'ru'

def _(telegram_id, key, **kwargs):
    lang = get_lang(telegram_id)
    text = T.get(lang, T['ru']).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

def get_address_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&accept-language=ru"
        response = requests.get(url, headers={'User-Agent': 'VelosherBot/1.0'})
        if response.status_code == 200:
            data = response.json()
            if 'display_name' in data:
                return data['display_name']
    except:
        pass
    return f"{lat}, {lng}"

# ============ КЛАВИАТУРЫ ============

def main_keyboard(telegram_id):
    lang = get_lang(telegram_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton("🛍️ Каталог", url=f"{WEB_URL}/shop/"),
            InlineKeyboardButton("🛒 Корзина", url=f"{WEB_URL}/shop/"),
            InlineKeyboardButton("👤 Мой профиль", callback_data="show_profile"),
            InlineKeyboardButton("📋 Мои заказы", callback_data="show_orders"),
            InlineKeyboardButton("🌐 Сменить язык", callback_data="change_lang"),
            InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("🛍️ Katalog", url=f"{WEB_URL}/shop/"),
            InlineKeyboardButton("🛒 Savat", url=f"{WEB_URL}/shop/"),
            InlineKeyboardButton("👤 Mening profilim", callback_data="show_profile"),
            InlineKeyboardButton("📋 Mening buyurtmalarim", callback_data="show_orders"),
            InlineKeyboardButton("🌐 Tilni o'zgartirish", callback_data="change_lang"),
            InlineKeyboardButton("ℹ️ Yordam", callback_data="show_help")
        )
    
    return keyboard

def back_keyboard(telegram_id):
    lang = get_lang(telegram_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    text = "🔙 Назад" if lang == 'ru' else "🔙 Orqaga"
    keyboard.add(InlineKeyboardButton(text, callback_data="back_to_menu"))
    return keyboard

def location_keyboard(telegram_id):
    lang = get_lang(telegram_id)
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if lang == 'ru':
        keyboard.add(KeyboardButton("📍 Отправить локацию", request_location=True))
        keyboard.add(KeyboardButton("❌ Отмена"))
    else:
        keyboard.add(KeyboardButton("📍 Joylashuv yuborish", request_location=True))
        keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard

def phone_keyboard(telegram_id):
    lang = get_lang(telegram_id)
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if lang == 'ru':
        keyboard.add(KeyboardButton("📱 Отправить номер", request_contact=True))
        keyboard.add(KeyboardButton("❌ Отмена"))
    else:
        keyboard.add(KeyboardButton("📱 Raqam yuborish", request_contact=True))
        keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard

def lang_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="set_lang_uz")
    )
    return keyboard

user_states = {}

# ============ КОМАНДА START ============

@bot.message_handler(commands=['start'])
def start(message):
    telegram_id = str(message.from_user.id)
    user = get_user(telegram_id)
    
    if user and user.get('location_lat'):
        text = _(telegram_id, 'menu')
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_keyboard(telegram_id))
        return
    
    if not user or not user.get('language'):
        bot.send_message(message.chat.id, "🌐 *Выберите язык / Tilni tanlang:*", parse_mode='Markdown', reply_markup=lang_keyboard())
        return
    
    user_states[telegram_id] = {'step': 'location', 'data': {}}
    text = _(telegram_id, 'ask_location')
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=location_keyboard(telegram_id))

# ============ ВЫБОР ЯЗЫКА ============

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
def set_language(call):
    lang = call.data.split('_')[2]
    telegram_id = str(call.from_user.id)
    user = get_user(telegram_id)
    
    if user and user.get('location_lat'):
        update_language(telegram_id, lang)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        address = user.get('location', 'Не указан')
        if user.get('location_lat') and user.get('location_lng'):
            try:
                addr = get_address_from_coords(user['location_lat'], user['location_lng'])
                if addr: address = addr
            except: pass
        text = _(telegram_id, 'profile_ok', name=user.get('first_name', 'Не указано'), phone=user.get('phone', 'Не указан'), address=address)
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=main_keyboard(telegram_id))
        send_user_to_web(telegram_id)
        return
    
    if user:
        update_language(telegram_id, lang)
    else:
        save_user({'telegram_id': telegram_id, 'username': call.from_user.username or '', 'first_name': call.from_user.first_name or '', 'language': lang})
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_states[telegram_id] = {'step': 'location', 'data': {'language': lang}}
    text = _(telegram_id, 'ask_location')
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=location_keyboard(telegram_id))

# ============ ПРОФИЛЬ ============

@bot.callback_query_handler(func=lambda call: call.data == "show_profile")
def show_profile(call):
    telegram_id = str(call.from_user.id)
    user = get_user(telegram_id)
    
    if not user:
        text = "❌ Профиль не найден. Нажмите /start"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        return
    
    lang_names = {'ru': 'Русский', 'uz': "O'zbekcha"}
    lang_display = lang_names.get(user.get('language', 'ru'), 'Русский')
    
    address = user.get('location', 'Не указан')
    if user.get('location_lat') and user.get('location_lng'):
        try:
            addr = get_address_from_coords(user['location_lat'], user['location_lng'])
            if addr: address = addr
        except: pass
    
    text = _(telegram_id, 'profile_info',
             id=telegram_id,
             name=user.get('first_name', 'Не указано'),
             phone=user.get('phone', 'Не указан'),
             address=address,
             orders=user.get('total_orders', 0),
             lang=lang_display)
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    lang = get_lang(telegram_id)
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton("📍 Изменить локацию", callback_data="change_location"),
            InlineKeyboardButton("📱 Изменить номер", callback_data="change_phone"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("📍 Joylashuvni o'zgartirish", callback_data="change_location"),
            InlineKeyboardButton("📱 Raqamni o'zgartirish", callback_data="change_phone"),
            InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")
        )
    
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "change_location")
def change_location(call):
    telegram_id = str(call.from_user.id)
    lang = get_lang(telegram_id)
    text = "📍 *Отправьте новую локацию*" if lang == 'ru' else "📍 *Yangi joylashuvni yuboring*"
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=location_keyboard(telegram_id))
    user_states[telegram_id] = {'step': 'change_location'}

@bot.callback_query_handler(func=lambda call: call.data == "change_phone")
def change_phone(call):
    telegram_id = str(call.from_user.id)
    lang = get_lang(telegram_id)
    text = "📱 *Введите новый номер телефона:*" if lang == 'ru' else "📱 *Yangi telefon raqamini kiriting:*"
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    user_states[telegram_id] = {'step': 'change_phone'}

# ============ ОСТАЛЬНЫЕ КОЛБЭКИ ============

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    telegram_id = str(call.from_user.id)
    if telegram_id in user_states:
        del user_states[telegram_id]
    text = _(telegram_id, 'menu')
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='Markdown',
        reply_markup=main_keyboard(telegram_id)
    )

@bot.callback_query_handler(func=lambda call: call.data == "change_lang")
def change_lang_from_menu(call):
    bot.send_message(call.message.chat.id, "🌐 *Выберите язык / Tilni tanlang:*", parse_mode='Markdown', reply_markup=lang_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "show_orders")
def show_orders(call):
    telegram_id = str(call.from_user.id)
    try:
        response = requests.get(f"{WEB_URL}/api/orders?telegram_id={telegram_id}")
        data = response.json()
        orders = data.get('orders', [])
        if not orders:
            text = _(telegram_id, 'no_orders')
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=back_keyboard(telegram_id))
            return
        
        text = "📋 *Ваши заказы:*\n\n"
        for order in orders[:5]:
            status_emoji = {'pending': '⏳', 'paid': '✅', 'shipped': '🚚', 'delivered': '📦', 'cancelled': '❌'}.get(order.get('status'), '❓')
            text += f"{status_emoji} *Заказ #{order.get('order_id')}*\n"
            text += f"📅 {order.get('created_at', '')[:16]}\n"
            text += f"💰 {int(order.get('total_amount', 0)):,} сум\n\n"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=back_keyboard(telegram_id))
    except:
        text = _(telegram_id, 'no_orders')
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=back_keyboard(telegram_id))

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def show_help(call):
    telegram_id = str(call.from_user.id)
    admin_url = f"{WEB_URL}/admin/"
    text = _(telegram_id, 'help_text', admin_url=admin_url)
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=back_keyboard(telegram_id))

# ============ ОБРАБОТКА СООБЩЕНИЙ ============

@bot.message_handler(content_types=['location'])
def handle_location(message):
    telegram_id = str(message.from_user.id)
    
    if telegram_id in user_states and user_states[telegram_id].get('step') == 'change_location':
        lat = message.location.latitude
        lng = message.location.longitude
        address = f"{lat}, {lng}"
        try:
            addr = get_address_from_coords(lat, lng)
            if addr: address = addr
        except: pass
        
        user = get_user(telegram_id)
        if user:
            user['location'] = address
            user['location_lat'] = str(lat)
            user['location_lng'] = str(lng)
            save_user(user)
            send_user_to_web(telegram_id)
        
        del user_states[telegram_id]
        lang = get_lang(telegram_id)
        text = "✅ *Локация обновлена!*" if lang == 'ru' else "✅ *Joylashuv yangilandi!*"
        bot.reply_to(message, text, parse_mode='Markdown')
        show_profile(message)
        return
    
    if telegram_id not in user_states or user_states[telegram_id].get('step') != 'location':
        return
    
    lat = message.location.latitude
    lng = message.location.longitude
    address = f"{lat}, {lng}"
    try:
        addr = get_address_from_coords(lat, lng)
        if addr: address = addr
    except: pass
    
    user_states[telegram_id]['data']['location'] = address
    user_states[telegram_id]['data']['location_lat'] = str(lat)
    user_states[telegram_id]['data']['location_lng'] = str(lng)
    user_states[telegram_id]['step'] = 'name'
    text = _(telegram_id, 'location_ok')
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text and m.text not in ["❌ Отмена", "❌ Bekor qilish"])
def handle_text(message):
    telegram_id = str(message.from_user.id)
    
    if telegram_id in user_states and user_states[telegram_id].get('step') == 'change_phone':
        phone = re.sub(r'[^0-9+]', '', message.text)
        if len(phone) < 10:
            lang = get_lang(telegram_id)
            error_msg = "❌ Неверный формат. Введите номер еще раз:" if lang == 'ru' else "❌ Noto'g'ri format. Qayta kiriting:"
            bot.reply_to(message, error_msg)
            return
        
        user = get_user(telegram_id)
        if user:
            user['phone'] = phone
            save_user(user)
            send_user_to_web(telegram_id)
        
        del user_states[telegram_id]
        lang = get_lang(telegram_id)
        text = "✅ *Номер обновлен!*" if lang == 'ru' else "✅ *Raqam yangilandi!*"
        bot.reply_to(message, text, parse_mode='Markdown')
        show_profile(message)
        return
    
    if telegram_id not in user_states:
        return
    
    step = user_states[telegram_id].get('step')
    
    if step == 'name':
        user_states[telegram_id]['data']['first_name'] = message.text
        user_states[telegram_id]['step'] = 'phone'
        text = _(telegram_id, 'name_ok')
        bot.reply_to(message, text, parse_mode='Markdown', reply_markup=phone_keyboard(telegram_id))
        return
    
    if step == 'phone':
        phone = re.sub(r'[^0-9+]', '', message.text)
        if len(phone) < 10:
            lang = get_lang(telegram_id)
            error_msg = "❌ Неверный формат. Введите номер еще раз:" if lang == 'ru' else "❌ Noto'g'ri format. Qayta kiriting:"
            bot.reply_to(message, error_msg)
            return
        
        user_states[telegram_id]['data']['phone'] = phone
        user_states[telegram_id]['step'] = 'done'
        data = user_states[telegram_id]['data']
        data['telegram_id'] = telegram_id
        data['username'] = message.from_user.username or ''
        save_user(data)
        send_user_to_web(telegram_id)
        
        address = data.get('location', 'Не указан')
        text = _(telegram_id, 'profile_ok', name=data.get('first_name', ''), phone=phone, address=address)
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_keyboard(telegram_id))
        del user_states[telegram_id]
        return

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    telegram_id = str(message.from_user.id)
    if telegram_id not in user_states or user_states[telegram_id].get('step') != 'phone':
        return
    
    phone = message.contact.phone_number
    user_states[telegram_id]['data']['phone'] = phone
    user_states[telegram_id]['step'] = 'done'
    data = user_states[telegram_id]['data']
    data['telegram_id'] = telegram_id
    data['username'] = message.from_user.username or ''
    save_user(data)
    send_user_to_web(telegram_id)
    
    address = data.get('location', 'Не указан')
    text = _(telegram_id, 'profile_ok', name=data.get('first_name', ''), phone=phone, address=address)
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_keyboard(telegram_id))
    del user_states[telegram_id]

@bot.message_handler(func=lambda m: m.text in ["❌ Отмена", "❌ Bekor qilish"])
def cancel(message):
    telegram_id = str(message.from_user.id)
    if telegram_id in user_states:
        del user_states[telegram_id]
    lang = get_lang(telegram_id)
    text = "❌ Отменено" if lang == 'ru' else "❌ Bekor qilindi"
    bot.reply_to(message, text)

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 Velosher Shop Бот")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("🚀 Запущен!")
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)