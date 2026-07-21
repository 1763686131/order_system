from flask import Flask, request, jsonify, send_from_directory # type: ignore
from flask_cors import CORS # type: ignore
import os
import json
import webbrowser
from datetime import datetime
from threading import Timer
import uuid  # 新增：用于生成唯一短码
import re    # 新增：用于清理文件名非法字符

# ------------------------------------------------
# 辅助函数：清理文件名中的非法字符（防崩溃核心）
# ------------------------------------------------
def sanitize_filename(text):
    if not text:
        return "未知"
    return re.sub(r'[\\/*?:"<>|\s]', "", str(text))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Username", "Role"]}})

USERS_FILE = '/app/data/users_db.json'
ORDERS_FILE = '/app/data/orders_db.json'
MATERIALS_FILE = '/app/data/material_db.json' 
BASE_UPLOAD_DIR = '/app/uploads' # 统一定义图片存储路径

if os.path.exists('/app/frontend/index.html'):
    FRONTEND_DIR = '/app/frontend'
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

FRONTEND_PATH = os.path.join(FRONTEND_DIR, 'index.html')

def read_users():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        d = [{"username": "1", "password": "741200", "role": "super_admin", "name": "系统超管"}, {"username": "2", "password": "123456", "role": "operator", "name": "默认测试员工"}]
        write_users(d)
        return d
    with open(USERS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def write_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)

def read_orders():
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    if not os.path.exists(ORDERS_FILE):
        ct = datetime.now().strftime('%Y-%m-%d %H:%M')
        d = {"orders": [{"id": 1, "title": "测试订单", "status": "pending", "type": 0, "date": ct, "completed_date": ""}]}
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
        if str(u['username']) == str(req_data.get('username')) and u['password'] == req_data.get('password'):
            return jsonify({
                "success": True, 
                "user": {
                    "username": u['username'], 
                    "name": u.get('name', u['username']),
                    "role": u['role'],
                    "permissions": u.get('permissions', [])
                }
            })
    return jsonify({"success": False, "message": "账号或密码错误"}), 401

@app.route('/api/users', methods=['GET'])
def get_all_users():
    return jsonify(read_users())

@app.route('/api/users', methods=['POST'])
def add_user():
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    
    req_data = request.json
    users_data = read_users()
    target_role = req_data.get('role', 'employee')
    
    if req_role == 'admin' and target_role in ['super_admin', 'admin']:
        return jsonify({"message": "越权操作：管理员只能创建员工账号"}), 403
        
    for u in users_data:
        if str(u['username']) == str(req_data.get('username')): return jsonify({"message": "账号已存在"}), 400
        
    users_data.append({
        "username": req_data.get('username'),
        "name": req_data.get('name', req_data.get('username')),
        "password": req_data.get('password'),
        "role": target_role,
        "permissions": req_data.get('permissions', [])
    })
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/users/<username>', methods=['DELETE'])
def delete_user(username):
    if request.headers.get('Role') != 'super_admin': return jsonify({"message": "越权：仅超级管理员可删除"}), 403
    users_data = read_users()
    users_data = [u for u in users_data if str(u['username']) != str(username)]
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/users/<username>/password', methods=['PUT'])
def update_user_password(username):
    if request.headers.get('Role') not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    req_data = request.json
    users_data = read_users()
    for u in users_data:
        if str(u['username']) == str(username):
            u['password'] = req_data.get('password')
            break
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/users/<username>/permissions', methods=['PUT'])
def update_user_permissions(username):
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']: return jsonify({"message": "权限不足"}), 403
    
    req_data = request.json
    perms = req_data.get('permissions', [])
    new_role = req_data.get('role')
    new_name = req_data.get('name') 
    
    users_data = read_users()
    for u in users_data:
        if str(u['username']) == str(username):
            if req_role == 'admin' and u['role'] in ['super_admin', 'admin']:
                return jsonify({"message": "越权：无权修改高级别账户"}), 403
            
            if req_role == 'admin':
                admin_restricted = ['pending.edit', 'pending.delete', 'completed.delete', 'material.edit', 'material.edit_stock', 'material.delete']
                old_perms = set(u.get('permissions', []))
                new_perms = set(perms)
                for restricted in admin_restricted:
                    if restricted in old_perms: new_perms.add(restricted)
                    else: new_perms.discard(restricted)
                perms = list(new_perms)

            u['permissions'] = perms
            if new_name is not None:
                u['name'] = new_name 
                
            if new_role and req_role == 'super_admin' and u['role'] != 'super_admin':
                u['role'] = new_role
            break
            
    write_users(users_data)
    return jsonify({"success": True})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders_data = read_orders()
    return jsonify(orders_data.get('orders', []))

@app.route('/api/orders', methods=['POST'])
def add_order():
    req_data = request.json
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    ct = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_id = max([x['id'] for x in orders_list], default=0) + 1
    
    new_order = {
        "id": new_id, 
        "title": req_data.get('title', ''), 
        "status": "pending", 
        "type": req_data.get('type', 0), 
        "date": ct, 
        "completed_date": "",
        "shipped_date": "",
        "shipping_method": "",
        "shipping_custom": "",
        "logistics_no": "",
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
def update_order_status(order_id):
    req_data = request.json
    ns = req_data.get('status')
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    for x in orders_list:
        if x['id'] == order_id:
            x['status'] = ns
            
            if ns == 'completed':
                x['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                x['shipped_date'] = ""
                x['shipping_method'] = ""
                x['shipping_custom'] = ""
                x['logistics_no'] = ""
                x['audit_state'] = 0
                
            elif ns == 'shipped':
                if 'audit_state' in req_data:
                    x['audit_state'] = req_data.get('audit_state', 0)
                else:
                    x['shipping_method'] = req_data.get('shipping_method', 4)
                    x['shipping_custom'] = req_data.get('shipping_custom', '')
                    x['logistics_no'] = req_data.get('logistics_no', '无单号记录')
                    x['shipped_date'] = req_data.get('shipped_date', datetime.now().strftime('%Y-%m-%d %H:%M'))
                    x['completed_date'] = x['shipped_date']
                    x['audit_state'] = 0 
                    
            elif ns == 'pending':
                x['completed_date'] = ""
                x['shipped_date'] = ""
                x['logistics_no'] = ""
                x['shipping_method'] = ""
                x['shipping_custom'] = ""
                x['audit_state'] = 0
            break
            
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    req_role = request.headers.get('Role')
    req_username = request.headers.get('Username')
    
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    
    target_order = next((o for o in orders_list if o['id'] == order_id), None)
    if not target_order: return jsonify({"message": "找不到订单"}), 404
    
    needed_perm = 'completed.delete' if target_order['status'] == 'completed' else 'pending.delete'
    
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
    req_data = request.json
    mat_data = read_materials()
    mat_data['total_stock'] = float(req_data.get('total_stock', 0))
    write_materials(mat_data)
    return jsonify({"success": True})

@app.route('/api/materials/<int:record_id>', methods=['PUT'])
def edit_material_record(record_id):
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
    mat_data = read_materials()
    mat_data['records'] = [x for x in mat_data.get('records', []) if x['id'] != record_id]
    write_materials(mat_data)
    return jsonify({"success": True})

# ==========================================
# 🚀 修复核心：带自动清理旧文件的回单上传引擎
# ==========================================
@app.route('/api/orders/<int:order_id>/upload_receipt', methods=['POST'])
def upload_receipt(order_id):
    file = request.files.get('receipt_image')
    if not file:
        return jsonify({"success": False, "message": "没有找到图片文件"}), 400

    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    order = next((o for o in orders_list if o.get('id') == order_id), None)
    
    if not order:
        return jsonify({"success": False, "message": "找不到该订单信息"}), 404

    # 🌟 ======= 新增核心：旧物理文件自动粉碎机 ======= 🌟
    old_img_url = order.get('receipt_img_url')
    if old_img_url and str(old_img_url).strip() != "":
        # 数据库里的路径长这样：/uploads/2026-07/xxx.jpg
        # 我们需要把它映射到后端的实际物理路径：/app/uploads/2026-07/xxx.jpg
        if old_img_url.startswith('/uploads/'):
            # 剥离前缀，拼接绝对路径
            relative_path = old_img_url.replace('/uploads/', '', 1)
            old_file_path = os.path.join(BASE_UPLOAD_DIR, relative_path)
            
            # 检查硬盘上是否存在这个文件，如果有，果断删除！
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                    print(f"✅ 成功粉碎废弃旧回单: {old_file_path}")
                except Exception as e:
                    print(f"⚠️ 删除旧回单失败，可能已被占用或手动删除: {e}")
    # 🌟 ================================================== 🌟

    client_name = sanitize_filename(order.get('order_client', '未知客户'))
    receiver_name = sanitize_filename(order.get('receiver_name', '未知收货人'))

    now = datetime.now() 
    month_folder = now.strftime("%Y-%m")      
    date_str = now.strftime("%Y-%m-%d")       
    
    target_dir = os.path.join(BASE_UPLOAD_DIR, month_folder)
    os.makedirs(target_dir, exist_ok=True)
    
    short_code = uuid.uuid4().hex[:4].upper() 
    file_ext = os.path.splitext(file.filename)[1] or '.jpg'
    
    safe_filename = f"{client_name}订单_{receiver_name}_{date_str}_{short_code}{file_ext}"
    save_path = os.path.join(target_dir, safe_filename)
    file.save(save_path)
    
    db_image_url = f"/uploads/{month_folder}/{safe_filename}"
    
    order['receipt_img_url'] = db_image_url
    write_orders(orders_data) 
    
    return jsonify({
        "success": True, 
        "message": "新图片上传并保存成功，旧图片已清理", 
        "image_url": db_image_url
    })

# ==========================================
# 🖼️ 新增回显接口：让前端能够读取刚才上传到 /app/uploads 的图片
# ==========================================
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(BASE_UPLOAD_DIR, filename)

# ==========================================
# 🎯 文件万能通配拦截器 (必须垫在所有特定路由的最后面)
# ==========================================
@app.route('/<path:path>')
def send_static_files(path): 
    return send_from_directory(FRONTEND_DIR, path)

def open_browser():
    if not os.path.exists('/app/frontend/index.html'): webbrowser.open("http://localhost:7899")

# ==========================================
# 🛑 主引擎启动 (必须永远放在文件的绝对最末尾)
# ==========================================
if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=7899, debug=False)