"""
运费记录管理 API 路由
100%从旧代码移植
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from utils.db_helper import read_freight_records, write_freight_records

freight_bp = Blueprint('freight', __name__, url_prefix='/api/freight-records')

@freight_bp.route('', methods=['GET'])
def get_freight_records():
    """获取所有运费记录"""
    data = read_freight_records()
    return jsonify(data.get('freight_records', []))

@freight_bp.route('', methods=['POST'])
def create_freight_record():
    """创建运费记录（审核时）"""
    req_data = request.json
    data = read_freight_records()

    record = {
        'id': str(uuid.uuid4()),
        'type': req_data.get('type'),
        'year': req_data.get('year'),
        'month': req_data.get('month'),
        'period': req_data.get('period'),
        'orders': req_data.get('orders', []),
        'totalAmount': req_data.get('totalAmount'),
        'reserveFund': req_data.get('reserveFund'),
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'createdBy': request.headers.get('Username', '管理员')
    }

    data['freight_records'].append(record)
    write_freight_records(data)

    return jsonify({'success': True, 'record': record})

@freight_bp.route('/reserve-fund', methods=['GET'])
def get_reserve_funds():
    """获取所有备用金记录"""
    data = read_freight_records()
    return jsonify(data.get('reserve_funds', []))

@freight_bp.route('/reserve-fund', methods=['POST'])
def create_reserve_fund():
    """创建备用金记录"""
    req_data = request.json
    data = read_freight_records()

    fund = {
        'id': str(uuid.uuid4()),
        'type': req_data.get('type'),
        'amount': float(req_data.get('amount')),
        'date': req_data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'note': req_data.get('note', ''),
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'createdBy': request.headers.get('Username', '管理员')
    }

    data['reserve_funds'].append(fund)
    write_freight_records(data)

    return jsonify({'success': True, 'fund': fund})

@freight_bp.route('/reserve-fund/latest', methods=['GET'])
def get_latest_reserve_fund():
    """获取最新的备用金余额"""
    data = read_freight_records()
    funds = data.get('reserve_funds', [])

    # 按日期和创建时间排序
    sorted_funds = sorted(funds, key=lambda x: (x.get('date', ''), x.get('createdAt', '')), reverse=True)

    if not sorted_funds:
        return jsonify({'balance': 0})

    # 计算当前余额
    balance = 0
    for fund in reversed(sorted_funds):
        if fund.get('type') == 'deposit':
            balance += fund.get('amount', 0)
        elif fund.get('type') == 'withdraw':
            balance -= fund.get('amount', 0)

    return jsonify({'balance': balance, 'latestRecord': sorted_funds[0] if sorted_funds else None})

@freight_bp.route('/reserve-fund/<fund_id>', methods=['PUT'])
def update_reserve_fund(fund_id):
    """更新备用金金额"""
    req_data = request.json
    data = read_freight_records()
    funds = data.get('reserve_funds', [])

    # 查找对应的备用金记录
    fund_index = None
    for i, fund in enumerate(funds):
        if fund.get('id') == fund_id:
            fund_index = i
            break

    if fund_index is None:
        return jsonify({'success': False, 'message': '备用金记录不存在'}), 404

    # 更新金额
    new_amount = float(req_data.get('amount', 0))
    funds[fund_index]['amount'] = new_amount
    funds[fund_index]['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    funds[fund_index]['updatedBy'] = request.headers.get('Username', '管理员')

    data['reserve_funds'] = funds
    write_freight_records(data)

    return jsonify({'success': True, 'fund': funds[fund_index]})
