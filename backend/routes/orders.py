"""
订单管理 API 路由
"""
from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime
import os
import uuid
import re
from utils.db_helper import read_orders, write_orders, read_users, orders_lock

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

BASE_UPLOAD_DIR = '/app/uploads'

def sanitize_filename(text):
    """清理文件名中的非法字符"""
    if not text:
        return "未知"
    return re.sub(r'[\\/*?:"<>|\s]', "", str(text))

def load_carrier_tags():
    """加载承运商标签"""
    CARRIER_TAGS_FILE = '/app/data/carrier_tags.json'
    if os.path.exists(CARRIER_TAGS_FILE):
        try:
            import json
            with open(CARRIER_TAGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_carrier_tags(tags):
    """保存承运商标签"""
    import json
    CARRIER_TAGS_FILE = '/app/data/carrier_tags.json'
    with open(CARRIER_TAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)

@orders_bp.route('', methods=['GET'])
def get_orders():
    """获取所有订单"""
    orders_data = read_orders()
    return jsonify(orders_data.get('orders', []))

@orders_bp.route('', methods=['POST'])
def add_order():
    """新增订单"""
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
        "items": req_data.get('items', []),
        "note": req_data.get('note', ''),
        "audit_state": 0,
        "creator": request.headers.get('Username', ''),
        "freight_costs": [],
        "receipt_url": "",
        "paid_amount": 0.0
    }

    orders_list.append(new_order)
    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"id": new_id, "order": new_order})

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
                    if 'logistics_no' in req_data:
                        x['logistics_no'] = req_data.get('logistics_no')
                    if 'freight_costs' in req_data:
                        x['freight_costs'] = req_data.get('freight_costs', [])
                else:
                    x['shipping_method'] = req_data.get('shipping_method', 4)
                    x['shipping_custom'] = req_data.get('shipping_custom', '')
                    x['logistics_no'] = req_data.get('logistics_no', '暂未录入单号')
                    x['shipped_date'] = req_data.get('shipped_date', datetime.now().strftime('%Y-%m-%d %H:%M'))
                    x['completed_date'] = x['shipped_date']
                    x['audit_state'] = 0
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
    if not target_order:
        return jsonify({"message": "找不到订单"}), 404

    needed_perm = 'completed.delete' if target_order['status'] == 'completed' else 'pending.delete'

    has_p = False
    if req_role == 'super_admin':
        has_p = True
    else:
        for u in read_users():
            if str(u['username']) == str(req_username):
                has_p = needed_perm in u.get('permissions', [])
                break

    if not has_p:
        return jsonify({"message": "底层权限不足，拦截删除操作"}), 403

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
    if req_role == 'super_admin':
        has_p = True
    else:
        for u in read_users():
            if str(u['username']) == str(req_username):
                has_p = 'completed.edit' in u.get('permissions', [])
                break

    if not has_p:
        return jsonify({"message": "权限不足"}), 403

    req_data = request.json
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])

    for x in orders_list:
        if x['id'] == order_id:
            x['title'] = req_data.get('title', x.get('title', ''))
            x['order_client'] = req_data.get('order_client', x.get('order_client', ''))
            x['receiver_name'] = req_data.get('receiver_name', x.get('receiver_name', ''))
            x['receiver_phone'] = req_data.get('receiver_phone', x.get('receiver_phone', ''))
            x['receiver_address'] = req_data.get('receiver_address', x.get('receiver_address', ''))
            x['items'] = req_data.get('items', x.get('items', []))
            x['note'] = req_data.get('note', x.get('note', ''))
            if 'type' in req_data:
                x['type'] = req_data['type']
                x['store_id'] = req_data['type']
            break

    orders_data['orders'] = orders_list
    write_orders(orders_data)
    return jsonify({"success": True})

@orders_bp.route('/<int:order_id>/upload_receipt', methods=['POST'])
def upload_receipt(order_id):
    """上传订单回单"""
    if 'receipt' not in request.files:
        return jsonify({"success": False, "message": "未找到上传文件"}), 400

    file = request.files['receipt']
    if file.filename == '':
        return jsonify({"success": False, "message": "未选择文件"}), 400

    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    target_order = next((o for o in orders_list if o['id'] == order_id), None)

    if not target_order:
        return jsonify({"success": False, "message": "订单不存在"}), 404

    # 生成文件名
    ext = os.path.splitext(file.filename)[1]
    order_title = sanitize_filename(target_order.get('title', ''))
    short_uuid = str(uuid.uuid4())[:8]
    filename = f"{order_id}_{order_title}_{short_uuid}{ext}"

    # 保存文件
    upload_dir = os.path.join(BASE_UPLOAD_DIR, 'receipts')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # 更新订单
    target_order['receipt_url'] = f"/uploads/receipts/{filename}"
    write_orders(orders_data)

    return jsonify({"success": True, "url": target_order['receipt_url']})

@orders_bp.route('/<int:order_id>/receipt', methods=['DELETE'])
def delete_receipt(order_id):
    """删除订单回单"""
    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])
    target_order = next((o for o in orders_list if o['id'] == order_id), None)

    if not target_order:
        return jsonify({"success": False, "message": "订单不存在"}), 404

    receipt_url = target_order.get('receipt_url', '')
    if receipt_url:
        filepath = os.path.join('/app', receipt_url.lstrip('/'))
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

    target_order['receipt_url'] = ""
    write_orders(orders_data)

    return jsonify({"success": True})

@orders_bp.route('/<int:order_id>/paid-amount', methods=['PUT'])
def update_paid_amount(order_id):
    """更新订单已付款金额"""
    req_data = request.json
    paid_amount = req_data.get('paid_amount', 0.0)

    orders_data = read_orders()
    orders_list = orders_data.get('orders', [])

    for order in orders_list:
        if order['id'] == order_id:
            order['paid_amount'] = float(paid_amount)
            break

    orders_data['orders'] = orders_list
    write_orders(orders_data)

    return jsonify({"success": True})

# 承运商标签相关
@orders_bp.route('/carrier_tags', methods=['GET'])
def get_carrier_tags():
    """获取承运商标签"""
    tags = load_carrier_tags()
    return jsonify(tags)

@orders_bp.route('/carrier_tags', methods=['POST'])
def add_carrier_tag():
    """添加承运商标签"""
    data = request.json or {}
    new_tag = (data.get('tag') or '').strip()
    if not new_tag:
        return jsonify({'success': False, 'message': '标签不能为空'}), 400

    tags = load_carrier_tags()
    if new_tag not in tags:
        tags.insert(0, new_tag)
        save_carrier_tags(tags[:20])

    return jsonify({'success': True, 'tags': tags})
