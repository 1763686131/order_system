"""
运费记录管理 API 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.db_helper import read_freight_records, write_freight_records

freight_bp = Blueprint('freight', __name__, url_prefix='/api/freight-records')

def generate_id():
    """生成唯一ID"""
    from datetime import datetime
    return int(datetime.now().timestamp() * 1000)

@freight_bp.route('', methods=['GET'])
def get_freight_records():
    """获取运费记录"""
    try:
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        db = read_freight_records()
        records = db.get('freight_records', [])

        if start_date and end_date:
            records = [r for r in records if start_date <= r.get('date', '') <= end_date]

        return jsonify(records)
    except Exception as e:
        return jsonify({'error': '获取运费记录失败'}), 500

@freight_bp.route('', methods=['POST'])
def create_freight_record():
    """创建运费记录"""
    try:
        db = read_freight_records()
        req_data = request.json

        record = {
            'id': generate_id(),
            'date': req_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'carrier': req_data.get('carrier', ''),
            'amount': float(req_data.get('amount', 0)),
            'note': req_data.get('note', ''),
            'paymentMethod': req_data.get('paymentMethod', 'cash'),
            'createdAt': datetime.now().isoformat(),
            'createdBy': request.headers.get('Username', '管理员')
        }

        db['freight_records'].append(record)
        write_freight_records(db)

        return jsonify({'success': True, 'record': record}), 201
    except Exception as e:
        return jsonify({'error': '创建运费记录失败'}), 500

@freight_bp.route('/<int:record_id>', methods=['PUT'])
def update_freight_record(record_id):
    """更新运费记录"""
    try:
        db = read_freight_records()
        records = db.get('freight_records', [])

        record = next((r for r in records if r['id'] == record_id), None)
        if not record:
            return jsonify({'error': '记录不存在'}), 404

        req_data = request.json
        record['date'] = req_data.get('date', record.get('date'))
        record['carrier'] = req_data.get('carrier', record.get('carrier'))
        record['amount'] = float(req_data.get('amount', record.get('amount')))
        record['note'] = req_data.get('note', record.get('note'))
        record['paymentMethod'] = req_data.get('paymentMethod', record.get('paymentMethod'))

        write_freight_records(db)
        return jsonify({'success': True, 'record': record})
    except Exception as e:
        return jsonify({'error': '更新运费记录失败'}), 500

@freight_bp.route('/<int:record_id>', methods=['DELETE'])
def delete_freight_record(record_id):
    """删除运费记录"""
    try:
        db = read_freight_records()
        records = db.get('freight_records', [])

        db['freight_records'] = [r for r in records if r['id'] != record_id]
        write_freight_records(db)

        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': '删除运费记录失败'}), 500

# 备用金相关
@freight_bp.route('/reserve-fund', methods=['GET'])
def get_reserve_funds():
    """获取备用金记录"""
    try:
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        db = read_freight_records()
        funds = db.get('reserve_funds', [])

        if start_date and end_date:
            funds = [f for f in funds if start_date <= f.get('date', '') <= end_date]

        return jsonify(funds)
    except Exception as e:
        return jsonify({'error': '获取备用金记录失败'}), 500

@freight_bp.route('/reserve-fund', methods=['POST'])
def create_reserve_fund():
    """创建备用金记录"""
    try:
        db = read_freight_records()
        req_data = request.json

        fund = {
            'id': generate_id(),
            'type': req_data.get('type'),
            'date': req_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'amount': float(req_data.get('amount')),
            'note': req_data.get('note', ''),
            'createdAt': datetime.now().isoformat(),
            'createdBy': request.headers.get('Username', '管理员')
        }

        db['reserve_funds'].append(fund)
        write_freight_records(db)

        return jsonify({'success': True, 'fund': fund})
    except Exception as e:
        return jsonify({'error': '录入备用金记录失败'}), 500

@freight_bp.route('/reserve-fund/<int:fund_id>', methods=['PUT'])
def update_reserve_fund(fund_id):
    """更新备用金记录"""
    try:
        db = read_freight_records()
        funds = db.get('reserve_funds', [])

        fund = next((f for f in funds if f['id'] == fund_id), None)
        if not fund:
            return jsonify({'error': '记录不存在'}), 404

        req_data = request.json
        fund['type'] = req_data.get('type', fund.get('type'))
        fund['date'] = req_data.get('date', fund.get('date'))
        fund['amount'] = float(req_data.get('amount', fund.get('amount')))
        fund['note'] = req_data.get('note', fund.get('note'))

        write_freight_records(db)
        return jsonify({'success': True, 'fund': fund})
    except Exception as e:
        return jsonify({'error': '更新备用金失败'}), 500

@freight_bp.route('/reserve-fund/<int:fund_id>', methods=['DELETE'])
def delete_reserve_fund(fund_id):
    """删除备用金记录"""
    try:
        db = read_freight_records()
        funds = db.get('reserve_funds', [])

        db['reserve_funds'] = [f for f in funds if f['id'] != fund_id]
        write_freight_records(db)

        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': '删除备用金失败'}), 500
