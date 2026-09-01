from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime

customers_bp = Blueprint('customers', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
CUSTOMERS_FILE = os.path.join(DATA_DIR, 'customers.json')

def read_customers():
    """读取客户数据"""
    # 如果文件不存在，返回空结构
    if not os.path.exists(CUSTOMERS_FILE):
        return {'customers': [], 'nextId': 1}

    try:
        with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取客户数据失败: {e}")
        return {'customers': [], 'nextId': 1}

def write_customers(data):
    """写入客户数据"""
    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        with open(CUSTOMERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写入客户数据失败: {e}")
        raise

@customers_bp.route('/', methods=['GET'])
def get_customers():
    """获取客户列表"""
    data = read_customers()
    customers = data.get('customers', [])

    # 获取查询参数
    customer_name = request.args.get('customerName', '')
    phone = request.args.get('phone', '')
    store_id = request.args.get('storeId', type=int)
    status = request.args.get('status', '')

    # 过滤
    filtered = customers
    if customer_name:
        filtered = [c for c in filtered if customer_name.lower() in c.get('customerName', '').lower()]
    if phone:
        filtered = [c for c in filtered if phone in c.get('phone', '')]
    if store_id:
        filtered = [c for c in filtered if c.get('storeId') == store_id]
    if status:
        filtered = [c for c in filtered if c.get('status') == status]

    return jsonify(filtered)

@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """获取单个客户详情"""
    data = read_customers()
    customers = data.get('customers', [])

    customer = next((c for c in customers if c['id'] == customer_id), None)
    if not customer:
        return jsonify({'error': '客户不存在'}), 404

    return jsonify(customer)

@customers_bp.route('/', methods=['POST'])
def create_customer():
    """创建客户"""
    req_data = request.json
    data = read_customers()

    customers = data.get('customers', [])
    next_id = data.get('nextId', 1)

    # 检查客户编号是否重复
    customer_code = req_data.get('customerCode', '')
    if any(c.get('customerCode') == customer_code for c in customers):
        return jsonify({'error': '客户编号已存在'}), 400

    # 创建新客户
    new_customer = {
        'id': next_id,
        'customerCode': customer_code,
        'customerName': req_data.get('customerName', ''),
        'storeId': req_data.get('storeId'),
        'contactPerson': req_data.get('contactPerson', ''),
        'phone': req_data.get('phone', ''),
        'address': req_data.get('address', ''),
        'balance': req_data.get('balance', 0),
        'receivable': req_data.get('initialDebt', 0),
        'bankName': req_data.get('bankName', ''),
        'bankAccount': req_data.get('bankAccount', ''),
        'bankCode': req_data.get('bankCode', ''),
        'taxNumber': req_data.get('taxNumber', ''),
        'remark': req_data.get('remark', ''),
        'status': 'active',
        'createdAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'updatedAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    }

    customers.append(new_customer)
    data['customers'] = customers
    data['nextId'] = next_id + 1

    write_customers(data)

    return jsonify(new_customer), 201

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """更新客户信息"""
    req_data = request.json
    data = read_customers()

    customers = data.get('customers', [])
    customer_index = next((i for i, c in enumerate(customers) if c['id'] == customer_id), None)

    if customer_index is None:
        return jsonify({'error': '客户不存在'}), 404

    # 更新客户信息
    customer = customers[customer_index]
    customer.update({
        'customerName': req_data.get('customerName', customer.get('customerName')),
        'customerCode': req_data.get('customerCode', customer.get('customerCode')),
        'storeId': req_data.get('storeId', customer.get('storeId')),
        'contactPerson': req_data.get('contactPerson', customer.get('contactPerson')),
        'phone': req_data.get('phone', customer.get('phone')),
        'address': req_data.get('address', customer.get('address')),
        'balance': req_data.get('balance', customer.get('balance')),
        'receivable': req_data.get('initialDebt', customer.get('receivable')),
        'bankName': req_data.get('bankName', customer.get('bankName')),
        'bankAccount': req_data.get('bankAccount', customer.get('bankAccount')),
        'bankCode': req_data.get('bankCode', customer.get('bankCode')),
        'taxNumber': req_data.get('taxNumber', customer.get('taxNumber')),
        'remark': req_data.get('remark', customer.get('remark')),
        'updatedAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    })

    customers[customer_index] = customer
    data['customers'] = customers

    write_customers(data)

    return jsonify(customer)

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """删除客户"""
    data = read_customers()
    customers = data.get('customers', [])

    customer_index = next((i for i, c in enumerate(customers) if c['id'] == customer_id), None)

    if customer_index is None:
        return jsonify({'error': '客户不存在'}), 404

    deleted_customer = customers.pop(customer_index)
    data['customers'] = customers

    write_customers(data)

    return jsonify({'success': True, 'message': '删除成功', 'customer': deleted_customer})
