from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = 'velosher-secret-key'
CORS(app)

DB_NAME = 'velosher.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # КАТЕГОРИИ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            name_uz TEXT,
            icon TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
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
            category_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # ПОЛЬЗОВАТЕЛИ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT,
            first_name TEXT,
            phone TEXT,
            address TEXT,
            location TEXT,
            location_lat TEXT,
            location_lng TEXT,
            language TEXT DEFAULT 'ru',
            total_orders INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
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
            location_lat TEXT,
            location_lng TEXT,
            products TEXT,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'card',
            payment_screenshot TEXT,
            comment TEXT,
            created_at TEXT,
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
    
    now = datetime.now().isoformat()
    
    # ДОБАВЛЯЕМ КАТЕГОРИИ
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        categories = [
            ('🏔️ Горные', 'Tog\' velosipedlari', 'fa-mountain', 1),
            ('🏙️ Городские', 'Shahar velosipedlari', 'fa-city', 2),
            ('🚴 Шоссейные', 'Shosse velosipedlari', 'fa-road', 3),
            ('⚡ Электро', 'E-velosipedlar', 'fa-bolt', 4),
            ('👶 Детские', 'Bollar velosipedlari', 'fa-child', 5),
            ('📦 Складные', 'Yig\'ma velosipedlar', 'fa-compress', 6)
        ]
        for cat in categories:
            cursor.execute('''
                INSERT INTO categories (name, name_uz, icon, sort_order, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (cat[0], cat[1], cat[2], cat[3], now))
    
    # ДОБАВЛЯЕМ ТОВАРЫ
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM categories WHERE name = '🏔️ Горные'")
        mountain_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE name = '🏙️ Городские'")
        city_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE name = '🚴 Шоссейные'")
        road_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM categories WHERE name = '⚡ Электро'")
        electric_id = cursor.fetchone()[0]
        
        products = [
            ('🚲 Горный XC-9000', 'Профессиональный горный велосипед', 4500000, 10, mountain_id),
            ('🚲 Горный Trail-500', 'Для бездорожья', 3500000, 8, mountain_id),
            ('🚲 City Pro', 'Комфортный городской', 2800000, 15, city_id),
            ('🚲 Comfort+', 'С крыльями', 2200000, 12, city_id),
            ('🚴 Speed-2000', 'Легкий шоссейник', 3800000, 6, road_id),
            ('🚴 Aero-Pro', 'Аэродинамичный', 5200000, 4, road_id),
            ('⚡ E-Bike 500W', 'Мощный мотор', 8900000, 3, electric_id),
            ('⚡ City-E', 'Для города', 6500000, 5, electric_id)
        ]
        for p in products:
            cursor.execute('''
                INSERT INTO products (name, description, price, stock, category_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            ''', (p[0], p[1], p[2], p[3], p[4], now))
    
    # ДОБАВЛЯЕМ АДМИНА
    cursor.execute('''
        INSERT OR IGNORE INTO users (telegram_id, username, first_name, phone, is_admin, created_at)
        VALUES ('6040186314', 'admin', 'Администратор', '+998901234567', 1, ?)
    ''', (now,))
    
    conn.commit()
    conn.close()
    print("✅ База данных готова!")

init_db()

# ============ API ============

@app.route('/api/products')
def api_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1
        ORDER BY p.id DESC
    ''')
    products = cursor.fetchall()
    conn.close()
    
    result = []
    for p in products:
        p = dict(p)
        result.append({
            'id': p['id'],
            'name': p['name'],
            'description': p['description'] or '',
            'price': p['price'],
            'stock': p['stock'],
            'image': p['image'] or '',
            'category': p['category_name'] or ''
        })
    return jsonify({'products': result})

@app.route('/api/categories')
def api_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order")
    cats = cursor.fetchall()
    conn.close()
    
    result = []
    for c in cats:
        c = dict(c)
        result.append({
            'id': c['id'],
            'name': c['name'],
            'icon': c['icon']
        })
    return jsonify({'categories': result})

@app.route('/api/category/add', methods=['POST'])
def api_add_category():
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO categories (name, name_uz, icon, sort_order, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (
            data.get('name'),
            data.get('name_uz', data.get('name')),
            data.get('icon', 'fa-tag'),
            data.get('sort_order', 0),
            now
        ))
        conn.commit()
        cat_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': cat_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/category/<int:cat_id>/delete', methods=['DELETE'])
def api_delete_category(cat_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE category_id = ?", (cat_id,))
        cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/product/add', methods=['POST'])
def api_add_product():
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO products (name, description, price, stock, image, category_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (
            data.get('name'),
            data.get('description', ''),
            data.get('price', 0),
            data.get('stock', 0),
            data.get('image', ''),
            data.get('category_id'),
            now,
            now
        ))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': product_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/product/<int:product_id>/delete', methods=['DELETE'])
def api_delete_product(product_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/user/<telegram_id>')
def api_get_user(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({'success': True, 'user': dict(user)})
    return jsonify({'success': False}), 404

@app.route('/api/user/save', methods=['POST'])
def api_save_user():
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        existing = cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (data.get('telegram_id'),)).fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE users SET username=?, first_name=?, phone=?, address=?, updated_at=?
                WHERE telegram_id=?
            ''', (
                data.get('username', ''),
                data.get('first_name', ''),
                data.get('phone', ''),
                data.get('address', ''),
                now,
                data.get('telegram_id')
            ))
        else:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, phone, address, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('telegram_id'),
                data.get('username', ''),
                data.get('first_name', ''),
                data.get('phone', ''),
                data.get('address', ''),
                now,
                now
            ))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/order/create', methods=['POST'])
def api_create_order():
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        order_id = f"{datetime.now().strftime('%Y%m%d')}{str(random.randint(1000, 9999))}"
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO orders (order_id, telegram_id, user_name, phone, address, products, total_amount, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        ''', (
            order_id,
            data.get('telegram_id'),
            data.get('user_name'),
            data.get('phone'),
            data.get('address'),
            json.dumps(data.get('products', [])),
            data.get('total_amount', 0),
            now,
            now
        ))
        conn.commit()
        order_db_id = cursor.lastrowid
        conn.close()
        
        # Отправляем в Telegram
        send_order_to_telegram(data, order_id)
        
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def send_order_to_telegram(data, order_id):
    try:
        BOT_TOKEN = "8954981282:AAFPuBkSQCqXfMWCtUyFfDIsVp0HhlarZLw"
        GROUP_ID = "-4983646908"
        
        products_text = ""
        for item in data.get('products', []):
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            total = price * quantity
            products_text += f"• {item.get('name', 'Товар')} × {quantity} = {int(total):,} сум\n"
        
        text = f"""
🆕 *НОВЫЙ ЗАКАЗ #{order_id}*

👤 *Покупатель:* {data.get('user_name', 'Не указан')}
📱 *Телефон:* {data.get('phone', 'Не указан')}
📍 *Адрес:* {data.get('address', 'Не указан')}

📦 *Товары:*
{products_text}
💰 *Итого:* {int(data.get('total_amount', 0)):,} сум

📅 *Дата:* {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': GROUP_ID, 'text': text, 'parse_mode': 'Markdown'}, timeout=5)
        print(f"✅ Заказ отправлен в группу {GROUP_ID}")
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")

@app.route('/api/upload/receipt', methods=['POST'])
def api_upload_receipt():
    try:
        # Создаем папку если нет
        os.makedirs('static/images/payments', exist_ok=True)
        
        file = request.files['receipt']
        order_id = request.form.get('order_id')
        telegram_id = request.form.get('telegram_id')
        
        if file:
            filename = f"receipt_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join('static/images/payments', filename)
            file.save(filepath)
            
            # Отправляем чек в Telegram
            try:
                BOT_TOKEN = "8954981282:AAFPuBkSQCqXfMWCtUyFfDIsVp0HhlarZLw"
                GROUP_ID = "-4983646908"
                with open(filepath, 'rb') as photo:
                    files = {'photo': photo}
                    data = {
                        'chat_id': GROUP_ID,
                        'caption': f"🧾 *Чек для заказа #{order_id}*\n👤 ID: {telegram_id}",
                        'parse_mode': 'Markdown'
                    }
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", files=files, data=data, timeout=10)
            except Exception as e:
                print(f"❌ Ошибка отправки чека: {e}")
            
            return jsonify({'success': True, 'filename': filename})
        return jsonify({'success': False, 'error': 'No file'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Velosher Shop Сервер запущен!")
    print("📍 http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
