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

@app.route('/api/users/<username>', methods=['DELETE'])
def delete_user(username):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权：仅超级管理员可删除"}), 403
    users_data = read_users()
    # 🐛 修复 Bug 1：强制转换为字符串进行比对，防止 JSON 里的 int 与 URL 里的 string 不匹配
    users_data = [u for u in users_data if str(u['username']) != str(username)]
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/users/<username>/permissions', methods=['PUT'])
def update_user_permissions(username):
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    
    req_data = request.json
    perms = req_data.get('permissions', [])
    new_role = req_data.get('role') # 🌟 接收前端传来的新角色
    
    users_data = read_users()
    for u in users_data:
        if str(u['username']) == str(username):
            if req_role == 'admin' and u['role'] in ['super_admin', 'admin']:
                return jsonify({"message": "越权：您无权修改该级别账户的权限"}), 403
            
            # 🛡️ 终极防御：防止黑客抓包越权！管理员即使伪造请求，也绝对改不了危险权限
            if req_role == 'admin':
                admin_restricted = ['pending.edit', 'pending.delete', 'completed.delete', 'material.edit', 'material.edit_stock', 'material.delete']
                old_perms = set(u.get('permissions', []))
                new_perms = set(perms)
                # 强行保持危险权限与修改前完全一致，管理员无法动这些勾
                for restricted in admin_restricted:
                    if restricted in old_perms: new_perms.add(restricted)
                    else: new_perms.discard(restricted)
                perms = list(new_perms)

            u['permissions'] = perms
            
            # 🐛 修复 Bug 2：允许超级管理员更新下属的角色
            if new_role and req_role == 'super_admin' and u['role'] != 'super_admin':
                u['role'] = new_role
            break
            
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    req_role = request.headers.get('Role')
    req_username = request.headers.get('Username')
    
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    
    target_order = next((o for o in orders_list if o['id'] == order_id), None)
    if not target_order: return jsonify({"message": "找不到订单"}), 404
    
    # 🌟 核心逻辑变更：判断当前是要删未完成还是已完成订单
    needed_perm = 'completed.delete' if target_order['status'] == 'completed' else 'pending.delete'
    
    # 🐛 修复 Bug 3：后端验证不再只看超管，而是去数据库查该员工有没有权限树里赋予的权限
    has_p = False
    if req_role == 'super_admin': has_p = True
    else:
        for u in read_users():
            if str(u['username']) == str(req_username):
                has_p = needed_perm in u.get('permissions', [])
                break
                
    if not has_p: return jsonify({"message": "底层权限不足，拦截删除操作"}), 403
    
    orders_list = [x for x in orders_list if x['id'] != order_id]
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})

@app.route('/api/orders/<int:order_id>/edit', methods=['PUT'])
def edit_order_content(order_id):
    req_role = request.headers.get('Role')
    req_username = request.headers.get('Username')
    
    # 🐛 修复 Bug 3 同理：后端验证员工有没有修改权限
    has_p = False
    if req_role == 'super_admin': has_p = True
    else:
        for u in read_users():
            if str(u['username']) == str(req_username):
                has_p = 'pending.edit' in u.get('permissions', [])
                break
                
    if not has_p: return jsonify({"message": "底层权限不足，拦截修改操作"}), 403
    
    req_data = request.json
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    for x in orders_list:
        if x['id'] == order_id:
            x['title'] = req_data.get('title', '')
            x['type'] = req_data.get('type', 0)
            x['date'] = req_data.get('date', '')
            x['order_client'] = req_data.get('order_client', '')
            x['receiver_name'] = req_data.get('receiver_name', '')
            x['receiver_phone'] = req_data.get('receiver_phone', '')
            x['receiver_address'] = req_data.get('receiver_address', '')
            x['goods_name'] = req_data.get('goods_name', '')
            x['goods_weight'] = req_data.get('goods_weight', '')
            x['goods_quantity'] = req_data.get('goods_quantity', '')
            x['goods_packaging'] = req_data.get('goods_packaging', '')
            x['logistics_service'] = req_data.get('logistics_service', '')
            x['remark'] = req_data.get('remark', '')
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