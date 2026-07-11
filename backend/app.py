from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import os
import json
import webbrowser
from datetime import datetime
from threading import Timer

app = Flask(__name__)

# 允许前端传输自定义的身份 Headers
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Username", "Role"]}})

USERS_FILE = '/app/data/users_db.json'
ORDERS_FILE = '/app/data/orders_db.json'

if os.path.exists('/app/frontend/index.html'):
    FRONTEND_DIR = '/app/frontend'
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

FRONTEND_PATH = os.path.join(FRONTEND_DIR, 'index.html')


def read_users():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        default_users = [
            {"username": "1", "password": "123456", "role": "super_admin"},
            {"username": "op01", "password": "123", "role": "operator"}
        ]
        write_users(default_users)
        return default_users
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def read_orders():
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    if not os.path.exists(ORDERS_FILE):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        default_orders = {
            "orders": [
                {"id": 1, "title": "测试中固大箱参数", "status": "pending", "type": 0, "date": current_time, "completed_date": ""},
                {"id": 2, "title": "测试绝缘垫片长文本", "status": "completed", "type": 1, "date": current_time, "completed_date": current_time}
            ]
        }
        write_orders(default_orders)
        return default_orders
    with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_orders(data):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- 🎯 终极修复：改用 Flask 官方高规格安全分发函数，彻底解决 Linux 图标引起的闪退重启 ---
@app.route('/<path:path>')
def send_static_files(path):
    # 自动安全分发静态文件，自动处理二进制流，避免死锁
    return send_from_directory(FRONTEND_DIR, path)


@app.route('/', methods=['GET'])
def index():
    if os.path.exists(FRONTEND_PATH):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    return f"<h3>错误：未找到前端网页！</h3>", 404


@app.route('/api/login', methods=['POST'])
def login():
    req_data = request.json
    username = str(req_data.get('username', '')).strip()
    password = str(req_data.get('password', '')).strip()
    users = read_users()
    user = next((u for u in users if u['username'] == username and u['password'] == password), None)
    if user:
        return jsonify({"success": True, "user": {"username": user['username'], "role": user['role']}})
    return jsonify({"success": False, "message": "账号或密码错误"}), 401


# --- 用户管理路由 ---
@app.route('/api/users', methods=['GET'])
def get_all_users():
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    return jsonify(read_users())

@app.route('/api/users', methods=['POST'])
def add_user():
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    req_data = request.json
    new_username = str(req_data.get('username', '')).strip()
    new_password = str(req_data.get('password', '')).strip()
    new_role = req_data.get('role', 'operator')
    if not new_username or not new_password: return jsonify({"message": "为空"}), 400
    users = read_users()
    if any(u['username'] == new_username for u in users): return jsonify({"message": "存在"}), 400
    users.append({"username": new_username, "password": new_password, "role": new_role})
    write_users(users)
    return jsonify({"success": True})

@app.route('/api/users/<string:username>/password', methods=['PUT'])
def change_user_password(username):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    req_data = request.json
    users = read_users()
    for u in users:
        if u['username'] == username:
            u['password'] = str(req_data.get('password')).strip()
            break
    write_users(users)
    return jsonify({"success": True})

@app.route('/api/users/<string:username>', methods=['DELETE'])
def delete_user(username):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    if username == '1': return jsonify({"message": "保护"}), 400
    users = read_users()
    users = [u for u in users if u['username'] != username]
    write_users(users)
    return jsonify({"success": True})


# --- 📋 订单核心接口 ---
@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify(read_orders().get('orders', []))


@app.route('/api/orders', methods=['POST'])
def add_order():
    username = request.headers.get('Username')
    role = request.headers.get('Role', 'operator')
    if str(username) == "1" or role in ['super_admin', 'admin']:
        req_data = request.json
        orders_data = read_orders()
        orders_list = orders_data.get('orders', [])
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_id = max([o['id'] for o in orders_list], default=0) + 1
        new_order = {
            "id": new_id, 
            "title": req_data.get('title'), 
            "status": "pending",
            "type": req_data.get('type', 0),  
            "date": current_time,
            "completed_date": ""  
        }
        orders_list.append(new_order)
        orders_data['orders'] = orders_list
        write_orders(orders_data)
        return jsonify({"success": True, "data": new_order})
    return jsonify({"success": False, "message": "权限不足"}), 403


@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    req_data = request.json
    new_status = req_data.get('status')
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    for order in orders_list:
        if order['id'] == order_id:
            order['status'] = new_status
            if new_status == 'completed':
                order['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            else:
                order['completed_date'] = ""
            break
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})


@app.route('/api/orders/<int:order_id>/edit', methods=['PUT'])
def edit_order_content(order_id):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    req_data = request.json
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    for order in orders_list:
        if order['id'] == order_id:
            order['title'] = req_data.get('title')
            order['type'] = req_data.get('type', 0)
            order['date'] = req_data.get('date')
            break
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    orders_list = [o for o in orders_list if o['id'] != order_id]
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})


def open_browser():
    if not os.path.exists('/app/frontend/index.html'):
        webbrowser.open("http://localhost:7899")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=7899, debug=False)