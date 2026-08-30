"""
订单管理 API 路由
100%从旧代码移植
"""
from flask import Blueprint, request, jsonify
from utils.db_helper import read_orders, write_orders, read_users
from datetime import datetime
import os
import uuid
import json
import threading

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

# 文件上传目录
if os.path.exists('/app/uploads'):
    BASE_UPLOAD_DIR = '/app/uploads'
else:
    BASE_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'uploads')

# 运营商标签文件路径
if os.path.exists('/app/data/carrier_tags.json'):
    CARRIER_TAGS_FILE = '/app/data/carrier_tags.json'
else:
    CARRIER_TAGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data', 'carrier_tags.json')

# 线程锁
orders_lock = threading.Lock()

def sanitize_filename(name):
    """文件名清理函数"""
    forbidden = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for ch in forbidden:
        name = name.replace(ch, '_')
    return name[:50]

def load_carrier_tags():
    """加载运营商标签"""
    if os.path.exists(CARRIER_TAGS_FILE):
        try:
            with open(CARRIER_TAGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_carrier_tags(tags):
    """保存运营商标签"""
    with open(CARRIER_TAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)

# ==========================================
# 订单接口
# ==========================================

@orders_bp.route('', methods=['GET'])
def get_orders():
    """获取所有订单"""
    orders_data = read_orders()
    return jsonify(orders_data.get('orders', []))

@orders_bp.route('', methods=['POST'])
def add_order():
    """创建新订单"""
    req_data = request.json
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    ct = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_id = max([x['id'] for x in orders_list], default=0) + 1

    new_order = {
        "id": new_id,
        "title": req_data.get('title', ''),
        "status": "pending",
        "type": req_data.get('type', 1),
        "store_id": req_data.get('type', 1),
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

@orders_bp.route('/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    """更新订单状态"""
    req_data = request.json
    ns = req_data.get('status')
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    for x in orders_list:
        if x['id'] == order_id:
            # 如果只是更新物流单号和运费，不改变状态
            if 'logistics_no' in req_data and 'status' not in req_data:
                x['logistics_no'] = req_data.get('logistics_no')
                if 'freight_costs' in req_data:
                    x['freight_costs'] = req_data.get('freight_costs', [])
                break

            # 正常的状态更新流程
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
                    # 🎯 核心修复：在审核操作时，必须接住前端传来的物流单号并更新进数据库！
                    if 'logistics_no' in req_data:
                        x['logistics_no'] = req_data.get('logistics_no')
                    # 保存运费数据
                    if 'freight_costs' in req_data:
                        x['freight_costs'] = req_data.get('freight_costs', [])
                else:
                    x['shipping_method'] = req_data.get('shipping_method', 4)
                    x['shipping_custom'] = req_data.get('shipping_custom', '')
                    x['logistics_no'] = req_data.get('logistics_no', '暂未录入单号')
                    x['shipped_date'] = req_data.get('shipped_date', datetime.now().strftime('%Y-%m-%d %H:%M'))
                    x['completed_date'] = x['shipped_date']
                    x['audit_state'] = 0
                    # 保存运费数据
                    if 'freight_costs' in req_data:
                        x['freight_costs'] = req_data.get('freight_costs', [])

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

@orders_bp.route('/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """删除订单"""
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

@orders_bp.route('/<int:order_id>/edit', methods=['PUT'])
def edit_order_content(order_id):
    """编辑订单内容"""
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
            x['type'] = req_data.get('type', 1)
            x['store_id'] = req_data.get('type', 1)
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

@orders_bp.route('/<int:order_id>/upload_receipt', methods=['POST'])
def upload_receipt(order_id):
    """上传订单回单"""
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

@orders_bp.route('/<int:order_id>/receipt', methods=['DELETE'])
def delete_order_receipt(order_id):
    """删除订单回单"""
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    order = next((o for o in orders_list if o.get('id') == order_id), None)

    if not order:
        return jsonify({"success": False, "message": "找不到该订单"}), 404

    old_img_url = order.get('receipt_img_url')
    if old_img_url and str(old_img_url).strip() != "":
        if old_img_url.startswith('/uploads/'):
            relative_path = old_img_url.replace('/uploads/', '', 1)
            old_file_path = os.path.join(BASE_UPLOAD_DIR, relative_path)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                    print(f"🗑️ 已彻底粉碎物理回单文件: {old_file_path}")
                except Exception as e:
                    print(f"⚠️ 删除物理文件失败: {e}")

    # 清空数据库中的回单路径值
    order['receipt_img_url'] = ""
    write_orders(orders_data)

    return jsonify({"success": True, "message": "回单图片已彻底删除"})

@orders_bp.route('/<int:order_id>/paid-amount', methods=['PUT'])
def update_order_paid_amount(order_id):
    """更新订单的已支付金额"""
    req_data = request.json

    with orders_lock:
        data = read_orders()
        orders = data.get('orders', [])

        # 查找对应的订单
        order_index = None
        for i, order in enumerate(orders):
            if order.get('id') == order_id:
                order_index = i
                break

        if order_index is None:
            return jsonify({'success': False, 'message': '订单不存在'}), 404

        order = orders[order_index]

        # 确保 freight_costs 数组存在
        if 'freight_costs' not in order or not isinstance(order['freight_costs'], list):
            order['freight_costs'] = []

        freight_cost_index = req_data.get('freightCostIndex', 0)
        paid_amount = float(req_data.get('paidAmount', 0))

        # 如果对应的运费记录不存在，创建一个
        if freight_cost_index >= len(order['freight_costs']):
            return jsonify({'success': False, 'message': '运费记录索引超出范围'}), 400

        # 更新已支付金额
        order['freight_costs'][freight_cost_index]['paid_amount'] = paid_amount
        order['freight_costs'][freight_cost_index]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order['freight_costs'][freight_cost_index]['updated_by'] = request.headers.get('Username', 'admin')

        orders[order_index] = order
        data['orders'] = orders
        write_orders(data)

    return jsonify({'success': True, 'order': order})

# ==========================================
# 运营商标签接口
# ==========================================

@orders_bp.route('/carrier_tags', methods=['GET'], endpoint='get_carrier_tags')
def get_carrier_tags():
    """获取运营商标签"""
    tags = load_carrier_tags()
    return jsonify(tags)

@orders_bp.route('/carrier_tags', methods=['POST'], endpoint='add_carrier_tag')
def add_carrier_tag():
    """添加运营商标签"""
    data = request.json or {}
    new_tag = (data.get('tag') or '').strip()
    if not new_tag:
        return jsonify({'success': False, 'message': '标签不能为空'}), 400

    tags = load_carrier_tags()
    if new_tag not in tags:
        tags.insert(0, new_tag)  # 最新输入的排在前面
        save_carrier_tags(tags[:20])  # 永远只保留最常用的前20个，防止词库爆炸

    return jsonify({'success': True, 'tags': tags})
