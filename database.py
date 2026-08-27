import sqlite3
import json
from datetime import datetime
import random
import os

DB_NAME = 'velosher.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # ПОЛЬЗОВАТЕЛИ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            address TEXT,
            location TEXT,
            location_lat TEXT,
            location_lng TEXT,
            language TEXT DEFAULT 'ru',
            theme TEXT DEFAULT 'light',
            total_orders INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            last_activity TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # ТОВАРЫ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            name_uz TEXT,
            description TEXT,
            description_uz TEXT,
            price REAL,
            old_price REAL,
            stock INTEGER DEFAULT 0,
            image TEXT,
            category TEXT,
            category_uz TEXT,
            is_active INTEGER DEFAULT 1,
            views INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # ЗАКАЗЫ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            telegram_id TEXT,
            user_name TEXT,
            phone TEXT,
            address TEXT,
            location TEXT,
            products TEXT,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'card',
            comment TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # КОРЗИНА
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            items TEXT,
            updated_at TEXT
        )
    ''')
    
    # СООБЩЕНИЯ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            username TEXT,
            first_name TEXT,
            message TEXT,
            is_admin INTEGER DEFAULT 0,
            is_read INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    # РАССЫЛКИ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            image TEXT,
            sent_to INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    # ДОБАВЛЯЕМ ТЕСТОВОГО АДМИНА
    cursor.execute('''
        INSERT OR IGNORE INTO users (telegram_id, username, first_name, phone, is_admin, created_at)
        VALUES ('6040186314', 'admin', 'Администратор', '+998901234567', 1, ?)
    ''', (datetime.now().isoformat(),))
    
    # ДОБАВЛЯЕМ ТЕСТОВЫЕ ТОВАРЫ
    cursor.execute('''
        INSERT OR IGNORE INTO products (name, description, price, stock, image, is_active, created_at)
        VALUES 
            ('🚲 Горный велосипед', 'Отличный горный велосипед для бездорожья', 1500000, 10, '', 1, ?),
            ('🚴 Шоссейный велосипед', 'Скоростной шоссейный велосипед', 2000000, 5, '', 1, ?),
            ('🚲 Детский велосипед', 'Для детей от 5 лет', 800000, 15, '', 1, ?)
    ''', (datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print("✅ База данных создана с тестовыми данными")

def get_user(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    users = cursor.fetchall()
    conn.close()
    return [dict(u) for u in users]

def save_user(data):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Проверяем существует ли
    existing = get_user(data.get('telegram_id'))
    
    if existing:
        cursor.execute('''
            UPDATE users SET
                username = ?,
                first_name = ?,
                last_name = ?,
                phone = ?,
                address = ?,
                location = ?,
                location_lat = ?,
                location_lng = ?,
                language = ?,
                theme = ?,
                total_orders = ?,
                total_spent = ?,
                is_admin = ?,
                last_activity = ?,
                updated_at = ?
            WHERE telegram_id = ?
        ''', (
            data.get('username', existing.get('username', '')),
            data.get('first_name', existing.get('first_name', '')),
            data.get('last_name', existing.get('last_name', '')),
            data.get('phone', existing.get('phone', '')),
            data.get('address', existing.get('address', '')),
            data.get('location', existing.get('location', '')),
            data.get('location_lat', existing.get('location_lat', '')),
            data.get('location_lng', existing.get('location_lng', '')),
            data.get('language', existing.get('language', 'ru')),
            data.get('theme', existing.get('theme', 'light')),
            data.get('total_orders', existing.get('total_orders', 0)),
            data.get('total_spent', existing.get('total_spent', 0)),
            data.get('is_admin', existing.get('is_admin', 0)),
            now,
            now,
            data.get('telegram_id')
        ))
    else:
        cursor.execute('''
            INSERT INTO users (
                telegram_id, username, first_name, last_name, phone, address,
                location, location_lat, location_lng, language, theme,
                total_orders, total_spent, is_admin, last_activity, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('telegram_id'),
            data.get('username', ''),
            data.get('first_name', 'Пользователь'),
            data.get('last_name', ''),
            data.get('phone', ''),
            data.get('address', ''),
            data.get('location', ''),
            data.get('location_lat', ''),
            data.get('location_lng', ''),
            data.get('language', 'ru'),
            data.get('theme', 'light'),
            data.get('total_orders', 0),
            data.get('total_spent', 0),
            data.get('is_admin', 0),
            now,
            now,
            now
        ))
    
    conn.commit()
    conn.close()
    return True

def get_products(lang='ru'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY id DESC")
    products = cursor.fetchall()
    conn.close()
    
    result = []
    for p in products:
        p = dict(p)
        result.append({
            'id': p['id'],
            'name': p.get('name' if lang == 'ru' else 'name_uz', p.get('name', '')),
            'description': p.get('description' if lang == 'ru' else 'description_uz', p.get('description', '')),
            'price': p['price'],
            'old_price': p['old_price'],
            'stock': p['stock'],
            'image': p['image'] or '',
            'category': p.get('category' if lang == 'ru' else 'category_uz', '')
        })
    return result

def add_product(data):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO products (
            name, name_uz, description, description_uz,
            price, old_price, stock, image, category, category_uz,
            is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('name', ''),
        data.get('name_uz', ''),
        data.get('description', ''),
        data.get('description_uz', ''),
        data.get('price', 0),
        data.get('old_price'),
        data.get('stock', 0),
        data.get('image', ''),
        data.get('category', 'Велосипеды'),
        data.get('category_uz', 'Velosipedlar'),
        data.get('is_active', 1),
        now,
        now
    ))
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id

def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def create_order(data):
    conn = get_db()
    cursor = conn.cursor()
    
    order_id = f"{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO orders (
            order_id, telegram_id, user_name, phone, address, location,
            products, total_amount, status, payment_method, comment, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_id,
        data.get('telegram_id'),
        data.get('user_name'),
        data.get('phone'),
        data.get('address'),
        data.get('location', ''),
        json.dumps(data.get('products', [])),
        data.get('total_amount', 0),
        data.get('status', 'pending'),
        data.get('payment_method', 'card'),
        data.get('comment', ''),
        now,
        now
    ))
    conn.commit()
    order_db_id = cursor.lastrowid
    conn.close()
    return order_db_id

def get_orders(telegram_id=None):
    conn = get_db()
    cursor = conn.cursor()
    
    if telegram_id:
        cursor.execute("SELECT * FROM orders WHERE telegram_id = ? ORDER BY id DESC", (telegram_id,))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    
    orders = cursor.fetchall()
    conn.close()
    return [dict(o) for o in orders]

def get_order_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM orders")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'")
    pending = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'paid'")
    paid = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(total_amount) as revenue FROM orders WHERE status = 'paid'")
    revenue = cursor.fetchone()['revenue'] or 0
    
    conn.close()
    return {'total': total, 'pending': pending, 'paid': paid, 'revenue': revenue}

def get_cart(session_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM carts WHERE session_id = ?", (session_id,))
    cart = cursor.fetchone()
    conn.close()
    if cart:
        return json.loads(cart['items'])
    return []

def save_cart(session_id, items):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO carts (session_id, items, updated_at)
        VALUES (?, ?, ?)
    ''', (session_id, json.dumps(items), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_message(data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (telegram_id, username, first_name, message, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('telegram_id'),
        data.get('username', ''),
        data.get('first_name', ''),
        data.get('message'),
        data.get('is_admin', 0),
        datetime.now().isoformat()
    ))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id

def get_messages(limit=100):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    messages = cursor.fetchall()
    conn.close()
    return [dict(m) for m in messages]

def save_broadcast(data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO broadcasts (message, image, sent_to, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        data.get('message'),
        data.get('image', ''),
        0,
        datetime.now().isoformat()
    ))
    conn.commit()
    broadcast_id = cursor.lastrowid
    conn.close()
    return broadcast_id

def get_broadcasts(limit=20):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM broadcasts ORDER BY id DESC LIMIT ?", (limit,))
    broadcasts = cursor.fetchall()
    conn.close()
    return [dict(b) for b in broadcasts]

# ИНИЦИАЛИЗАЦИЯ
init_db()
print("✅ База данных готова!")
print("👤 Админ создан: ID 6040186314")
print("🚲 Добавлены тестовые товары")