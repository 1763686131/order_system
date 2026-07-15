from flask import Flask, request, jsonify, Response, send_from_directory # type: ignore
from flask_cors import CORS # type: ignore
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


def read_users():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        d = [{"username": "1", "password": "741200", "role": "super_admin"}, {"username": "2return", "password": "123456", "role": "operator"}]
        write_users(d)
        return d
    with open(USERS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def write_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)


def read_orders():
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    if not os.path.exists(ORDERS_FILE):
        ct = datetime.now().strftime('%Y-%m-%d %H:%M')
        d = {"orders": [{"id": 1, "title": "测试中固大箱参数", "status": "pending", "type": 0, "date": ct, "completed_date": ""}]}
        write_orders(d)
        return d
    with open(ORDERS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def write_orders(data):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)


def read_materials():
    os.makedirs(os.path.dirname(MATERIALS_FILE), exist_ok=True)
    if not os.path.exists(MATERIALS_FILE):
        d = {"total_stock": 5000.0, "records": []} 
        write_materials(d)
        return d
    with open(MATERIALS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def write_materials(data):
    with open(MATERIALS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)


@app.route('/', methods=['GET'])
def index():
    if os.path.exists(FRONTEND_PATH): return send_from_directory(FRONTEND_DIR, 'index.html')
    return "<h3>错误：未找到前端网页！</h3>", 404

@app.route('/api/login', methods=['POST'])
def login():
    req_data = request.json
    users_data = read_users()
    for u in users_data:
        if u['username'] == req_data.get('username') and u['password'] == req_data.get('password'):
            # 🌟 核心修复：在这里把 permissions 数组一起打包返回给前端
            return jsonify({
                "success": True, 
                "user": {
                    "username": u['username'], 
                    "role": u['role'],
                    "permissions": u.get('permissions', [])  # <--- 就是少了这一句！
                }
            })
    return jsonify({"success": False, "message": "账号或密码错误"}), 401


# --- 用户管理路由 ---
@app.route('/api/users', methods=['GET'])
def get_all_users():
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    return jsonify(read_users())

@app.route('/api/users', methods=['POST'])
def add_user():
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    
    req_data = request.json
    users_data = read_users()
    target_role = req_data.get('role', 'employee')
    
    # 管理员只能创建普通员工，绝不能创建管理员或超级管理员
    if req_role == 'admin' and target_role in ['super_admin', 'admin']:
        return jsonify({"message": "越权操作：管理员只能创建员工账号"}), 403
        
    for u in users_data:
        if u['username'] == req_data.get('username'): return jsonify({"message": "账号已存在"}), 400
        
    users_data.append({
        "username": req_data.get('username'),
        "password": req_data.get('password'),
        "role": target_role,
        "permissions": req_data.get('permissions', []) # 🌟 新增保存权限数组
    })
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/users/<username>/password', methods=['PUT'])
def update_user_password(username):
    if request.headers.get('Role') not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    req_data = request.json
    users_data = read_users()
    for u in users_data:
        if u['username'] == username:
            u['password'] = req_data.get('password')
            break
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/users/<username>/permissions', methods=['PUT'])
def update_user_permissions(username):
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    
    perms = request.json.get('permissions', [])
    users_data = read_users()
    
    for u in users_data:
        if u['username'] == username:
            # 防御机制：管理员不能去改超级管理员和其他管理员的权限
            if req_role == 'admin' and u['role'] in ['super_admin', 'admin']:
                return jsonify({"message": "越权：您无权修改该级别账户的权限"}), 403
            u['permissions'] = perms
            break
            
    write_users(users_data)
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
    
    # 🌟 新增：接收所有的结构化字段
    new_order = {
        "id": new_id, 
        "title": req_data.get('title', ''), 
        "status": "pending", 
        "type": req_data.get('type', 0), 
        "date": ct, 
        "completed_date": "",
        "order_client": req_data.get('order_client', ''),
        "receiver_name": req_data.get('receiver_name', ''),
        "receiver_phone": req_data.get('receiver_phone', ''),
        "receiver_address": req_data.get('receiver_address', ''),
        "goods_name": req_data.get('goods_name', ''),
        "goods_weight": req_data.get('goods_weight', ''),
        "goods_quantity": req_data.get('goods_quantity', ''),
        "goods_packaging": req_data.get('goods_packaging', ''),
        "logistics_service": req_data.get('logistics_service', ''),
        "remark": req_data.get('remark', '')
    }
    
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
            # 状态如果是完成，就打上当前时间戳；如果是撤销未完成，就清空时间戳
            x['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M') if ns == 'completed' else ""
            break
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})

# ---------------------------------------------------

@app.route('/api/orders/<int:order_id>/edit', methods=['PUT'])
def edit_order_content(order_id):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权"}), 403
    req_data = request.json
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    for x in orders_list:
        if x['id'] == order_id:
            x['title'] = req_data.get('title', '')
            x['type'] = req_data.get('type', 0)
            x['date'] = req_data.get('date', '')
            # 新增：支持超级管理员修改结构化字段
            x['order_client'] = req_data.get('order_client', '')
            x['receiver_name'] = req_data.get('receiver_name', '')
            x['receiver_phone'] = req_data.get('receiver_phone', '')
            x['receiver_address'] = req_data.get('receiver_address', '')
            x['goods_name'] = req_data.get('goods_name', '')
            x['goods_weight'] = req_data.get('goods_weight', '')
            x['goods_quantity'] = req_data.get('goods_quantity', '')
            x['goods_packaging'] = req_data.get('goods_packaging', '')
            x['logistics_service'] = req_data.get('logistics_service', ''),
            x['remark'] = req_data.get('remark', '')
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


# --- 原材料持久化存储服务 API ---

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
        "date": ct,
        "remark": req_data.get('remark', '') 
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
            x['remark'] = str(req_data.get('remark', '')) 
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


# 🎯 文件万能通配拦截器已死死锁定在【最底部】，彻底解除与 API 请求抢道导致的 500 卡死
@app.route('/<path:path>')
def send_static_files(path): 
    return send_from_directory(FRONTEND_DIR, path)


def open_browser():
    if not os.path.exists('/app/frontend/index.html'): webbrowser.open("http://localhost:7899")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=7899, debug=False)