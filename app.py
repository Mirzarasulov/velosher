from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests
import uuid

from database import *

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

CORS(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

BOT_TOKEN = "8954981282:AAFPuBkSQCqXfMWCtUyFfDIsVp0HhlarZLw"
ADMIN_ID = "6040186314"
GROUP_ID = "-1004318807187"

# ============ СТРАНИЦЫ ============

@app.route('/')
def index():
    return redirect('/shop/')

@app.route('/shop/')
def shop():
    return render_template('shop.html')

@app.route('/product/<int:product_id>/')
def product_detail(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if not product:
        return redirect('/shop/')
    return render_template('product_detail.html', product=dict(product))

@app.route('/admin/')
def admin_panel():
    return render_template('admin/dashboard.html')

@app.route('/admin/orders/')
def admin_orders():
    return render_template('admin/orders.html')

@app.route('/admin/products/')
def admin_products():
    return render_template('admin/products.html')

@app.route('/admin/users/')
def admin_users():
    return render_template('admin/users.html')

@app.route('/admin/chat/')
def admin_chat():
    return render_template('admin/chat.html')

@app.route('/admin/broadcast/')
def admin_broadcast():
    return render_template('admin/broadcast.html')

# ============ API - ПОЛЬЗОВАТЕЛИ ============

@app.route('/api/user/<telegram_id>')
def api_get_user(telegram_id):
    user = get_user(telegram_id)
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'User not found'}), 404

@app.route('/api/users')
def api_get_users():
    users = get_all_users()
    return jsonify({'users': users})

@app.route('/api/user/save_from_bot', methods=['POST'])
def api_save_from_bot():
    data = request.json
    telegram_id = data.get('telegram_id')
    if not telegram_id:
        return jsonify({'error': 'telegram_id required'}), 400
    
    save_user(data)
    print(f"✅ Пользователь сохранен в БД: {telegram_id}")
    
    return jsonify({'success': True})

# ============ API - КОРЗИНА ============

@app.route('/api/cart', methods=['GET', 'POST'])
def api_cart():
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    
    if request.method == 'POST':
        data = request.json
        items = data.get('items', [])
        save_cart(session_id, items)
        return jsonify({'success': True})
    
    items = get_cart(session_id)
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
    
    response = jsonify({
        'items': items,
        'total': total,
        'count': len(items)
    })
    response.set_cookie('session_id', session_id, max_age=30*24*60*60)
    return response

# ============ API - ЗАКАЗЫ ============

@app.route('/api/orders')
def api_get_orders():
    telegram_id = request.args.get('telegram_id')
    orders = get_orders(telegram_id)
    
    for order in orders:
        if order.get('products'):
            try:
                if isinstance(order['products'], str):
                    order['products_list'] = json.loads(order['products'])
                else:
                    order['products_list'] = order['products']
            except:
                order['products_list'] = []
    
    return jsonify({'orders': orders})

@app.route('/api/orders/stats')
def api_get_order_stats():
    stats = get_order_stats()
    return jsonify(stats)

@app.route('/api/order/create', methods=['POST'])
def api_create_order():
    data = request.json
    order_id = create_order(data)
    
    # ========== ОТПРАВКА В TELEGRAM ==========
    send_order_to_telegram(data)
    
    return jsonify({'success': True, 'order_id': order_id})

def send_order_to_telegram(data):
    """Отправка заказа в Telegram группу"""
    try:
        products_text = ""
        for item in data.get('products', []):
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            total = price * quantity
            products_text += f"• {item.get('name', 'Товар')} × {quantity} = {int(total):,} сум\n"
        
        text = f"""
🆕 *НОВЫЙ ЗАКАЗ*

👤 *Покупатель:* {data.get('user_name', 'Не указан')}
📱 *Телефон:* {data.get('phone', 'Не указан')}
📍 *Адрес:* {data.get('address', 'Не указан')}
📍 *Локация:* {data.get('location', 'Не указана')}

📦 *Товары:*
{products_text}
💰 *Итого:* {int(data.get('total_amount', 0)):,} сум

💳 *Оплата:* Картой
📅 *Дата:* {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': GROUP_ID,
            'text': text,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            print(f"✅ Заказ отправлен в Telegram группу {GROUP_ID}")
        else:
            print(f"❌ Ошибка отправки: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")

# ============ API - ТОВАРЫ ============

@app.route('/api/products')
def api_get_products():
    products = get_products('ru')
    return jsonify({'products': products})

@app.route('/api/product/<int:product_id>')
def api_get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        return jsonify({'success': True, 'product': dict(product)})
    return jsonify({'success': False}), 404

@app.route('/api/products/add', methods=['POST'])
def api_add_product():
    try:
        name = request.form.get('name')
        name_uz = request.form.get('name_uz', name)
        description = request.form.get('description', '')
        description_uz = request.form.get('description_uz', '')
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
        category = request.form.get('category', 'Велосипеды')
        
        image_path = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_path = f"/static/images/products/{filename}"
        
        data = {
            'name': name,
            'name_uz': name_uz,
            'description': description,
            'description_uz': description_uz,
            'price': price,
            'stock': stock,
            'image': image_path,
            'category': category,
            'is_active': 1
        }
        
        product_id = add_product(data)
        return jsonify({'success': True, 'id': product_id, 'image': image_path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/products/<int:product_id>/delete', methods=['DELETE'])
def api_delete_product(product_id):
    delete_product(product_id)
    return jsonify({'success': True})

# ============ API - СООБЩЕНИЯ ============

@app.route('/api/messages')
def api_get_messages():
    limit = request.args.get('limit', 100, type=int)
    messages = get_messages(limit)
    return jsonify({'messages': messages})

@app.route('/api/messages/send', methods=['POST'])
def api_send_message():
    data = request.json
    msg_id = save_message(data)
    
    if data.get('telegram_id') and data.get('message'):
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': data.get('telegram_id'),
                'text': f"📩 *Сообщение от администратора:*\n\n{data.get('message')}",
                'parse_mode': 'Markdown'
            }
            requests.post(url, data=payload)
        except:
            pass
    
    return jsonify({'success': True, 'id': msg_id})

@app.route('/api/messages/read/all', methods=['POST'])
def api_mark_all_read():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET is_read = 1")
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ============ API - РАССЫЛКА ============

@app.route('/api/broadcast/send', methods=['POST'])
def api_send_broadcast():
    try:
        message = request.form.get('message')
        image = request.files.get('image')
        
        image_path = ''
        if image and image.filename:
            ext = image.filename.rsplit('.', 1)[1].lower()
            filename = f"broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            filepath = os.path.join('static/images/broadcasts', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            image.save(filepath)
            image_path = f"/static/images/broadcasts/{filename}"
        
        broadcast_data = {'message': message, 'image': image_path}
        save_broadcast(broadcast_data)
        
        users = get_all_users()
        sent_count = 0
        
        for user in users:
            telegram_id = user.get('telegram_id')
            if not telegram_id:
                continue
            
            try:
                if image_path:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                    with open(filepath, 'rb') as photo:
                        files = {'photo': photo}
                        data = {'chat_id': telegram_id, 'caption': message, 'parse_mode': 'Markdown'}
                        requests.post(url, files=files, data=data)
                else:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {'chat_id': telegram_id, 'text': message, 'parse_mode': 'Markdown'}
                    requests.post(url, data=payload)
                sent_count += 1
            except Exception as e:
                print(f"Ошибка отправки пользователю {telegram_id}: {e}")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE broadcasts SET sent_to = ? WHERE id = (SELECT MAX(id) FROM broadcasts)", (sent_count,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'sent': sent_count, 'total': len(users)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/broadcasts')
def api_get_broadcasts():
    broadcasts = get_broadcasts()
    return jsonify({'broadcasts': broadcasts})

# ============ API - СТАТИСТИКА ============

@app.route('/api/stats')
def api_get_stats():
    users = len(get_all_users())
    orders_data = get_order_stats()
    return jsonify({
        'users': users,
        'orders': orders_data['total'],
        'pending_orders': orders_data['pending'],
        'paid_orders': orders_data['paid'],
        'revenue': orders_data['revenue']
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Velosher Shop Сервер запущен!")
    print(f"📱 BOT_TOKEN: {BOT_TOKEN[:20]}...")
    print(f"📢 GROUP_ID: {GROUP_ID}")
    print("📍 http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)