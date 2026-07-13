from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import os
import json
import webbrowser
from datetime import datetime
from threading import Timer

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Username", "Role"]}})

USERS_FILE = '/app/data/users_db.json'
ORDERS_FILE = '/app/data/orders_db.json'
MATERIALS_FILE = '/app/data/material_db.json' 

if os.path.exists('/app/frontend/index.html'):
    FRONTEND_DIR = '/app/frontend'
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

FRONTEND_PATH = os.path.join(FRONTEND_DIR, 'index.html')


# ---------------------------------------------------------
# 🎯 核心升级：工业级防弹数据库自愈逻辑
# 不管数据库是被清空、乱码还是损坏，瞬间自动重建，免去手动删除烦恼
# ---------------------------------------------------------
def read_users():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    default_data = [{"username": "1", "password": "123456", "role": "super_admin"}, {"username": "op01", "password": "123", "role": "operator"}]
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data or not isinstance(data, list): raise ValueError()
            return data
    except Exception:
        write_users(default_data)
        return default_data

def write_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)


def read_orders():
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    ct = datetime.now().strftime('%Y-%m-%d %H:%M')
    default_data = {"orders": [{"id": 1, "title": "测试中固大箱参数", "status": "pending", "type": 0, "date": ct, "completed_date": ""}]}
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data or 'orders' not in data: raise ValueError()
            return data
    except Exception:
        write_orders(default_data)
        return default_data

def write_orders(data):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)


def read_materials():
    os.makedirs(os.path.dirname(MATERIALS_FILE), exist_ok=True)
    default_data = {"total_stock": 5000.0, "records": []} 
    try:
        with open(MATERIALS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data or 'total_stock' not in data: raise ValueError()
            return data
    except Exception:
        write_materials(default_data)
        return default_data

def write_materials(data):
    with open(MATERIALS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
# ---------------------------------------------------------


@app.route('/', methods=['GET'])
def index():
    if os.path.exists(FRONTEND_PATH): return send_from_directory(FRONTEND_DIR, 'index.html')
    return "<h3>错误：未找到前端网页！</h3>", 404

@app.route('/api/login', methods=['POST'])
def login():
    req_data = request.json
    u, p = str(req_data.get('username', '')).strip(), str(req_data.get('password', '')).strip()
    users = read_users()
    user = next((x for x in users if x['username'] == u and x['password'] == p), None)
    if user: return jsonify({"success": True, "user": {"username": user['username'], "role": user['role']}})
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
    nu, np, nr = str(req_data.get('username', '')).strip(), str(req_data.get('password', '')).strip(), req_data.get('role', 'operator')
    if not nu or not np: return jsonify({"message": "为空"}), 400
    users = read_users()
    if any(x['username'] == nu for x in users): return jsonify({"message": "存在"}), 400
    users.append({"username": nu, "password": np, "role": nr})
    write_users(users)
    return jsonify({"success": True})

@app.route('/api/users/<string:username>/password', methods=['PUT'])
def change_user_password(username):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    p = str(request.json.get('password')).strip()
    users = read_users()
    for x in users:
        if x['username'] == username: x['password'] = p; break
    write_users(users)
    return jsonify({"success": True})

@app.route('/api/users/<string:username>', methods=['DELETE'])
def delete_user(username):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    if username == '1': return jsonify({"message": "保护"}), 400
    users = read_users()
    users = [x for x in users if x['username'] != username]
    write_users(users)
    return jsonify({"success": True})


# --- 📋 订单核心接口 ---
@app.route('/api/orders', methods=['GET'])
def get_orders(): return jsonify(read_orders().get('orders', []))

@app.route('/api/orders', methods=['POST'])
def add_order():
    if request.headers.get('Role') not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    req_data = request.json
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    ct = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_id = max([x['id'] for x in orders_list], default=0) + 1
    new_order = {"id": new_id, "title": req_data.get('title'), "status": "pending", "type": req_data.get('type', 0), "date": ct, "completed_date": ""}
    orders_list.append(new_order)
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True, "data": new_order})

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    ns = request.json.get('status')
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    for x in orders_list:
        if x['id'] == order_id:
            x['status'] = ns
            x['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M') if ns == 'completed' else ""
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
    for x in orders_list:
        if x['id'] == order_id:
            x['title'] = req_data.get('title')
            x['type'] = req_data.get('type', 0)
            x['date'] = req_data.get('date')
            break
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    orders_data = read_orders()
    orders_data['orders'] = [x for x in orders_data.get('orders', []) if x['id'] != order_id]
    write_orders(orders_data)
    return jsonify({"success": True})


# --- 🏭 原材料持久化存储服务 API ---

@app.route('/api/materials', methods=['GET'])
def get_materials():
    return jsonify(read_materials())

@app.route('/api/materials', methods=['POST'])
def add_material_record():
    req_data = request.json
    mat_data = read_materials()
    records_list = mat_data.get('records', [])
    ct = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_id = max([x['id'] for x in records_list], default=0) + 1
    new_record = {
        "id": new_id,
        "used": float(req_data.get('used', 0)),
        "produced": float(req_data.get('produced', 0)),
        "date": ct
    }
    records_list.append(new_record)
    mat_data['records'] = records_list
    write_materials(mat_data) 
    return jsonify({"success": True})

@app.route('/api/materials/stock', methods=['PUT'])
def update_total_stock():
    if request.headers.get('Role') not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    req_data = request.json
    mat_data = read_materials()
    mat_data['total_stock'] = float(req_data.get('total_stock', 0))
    write_materials(mat_data)
    return jsonify({"success": True})

@app.route('/api/materials/<int:record_id>', methods=['PUT'])
def edit_material_record(record_id):
    if request.headers.get('Role') not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    req_data = request.json
    mat_data = read_materials()
    for x in mat_data.get('records', []):
        if x['id'] == record_id:
            x['used'] = float(req_data.get('used', 0))
            x['produced'] = float(req_data.get('produced', 0))
            break
    write_materials(mat_data)
    return jsonify({"success": True})

@app.route('/api/materials/<int:record_id>', methods=['DELETE'])
def delete_material_record(record_id):
    if request.headers.get('Role') not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    mat_data = read_materials()
    mat_data['records'] = [x for x in mat_data.get('records', []) if x['id'] != record_id]
    write_materials(mat_data)
    return jsonify({"success": True})


@app.route('/<path:path>')
def send_static_files(path): 
    return send_from_directory(FRONTEND_DIR, path)


def open_browser():
    if not os.path.exists('/app/frontend/index.html'): webbrowser.open("http://localhost:7899")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=7899, debug=False)