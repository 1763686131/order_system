"""
门店管理 API 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.db_helper import read_stores, write_stores

stores_bp = Blueprint('stores', __name__, url_prefix='/api/stores')

@stores_bp.route('', methods=['GET'])
def get_stores():
    """获取所有门店"""
    try:
        stores = read_stores()
        return jsonify(stores)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stores_bp.route('/<int:store_id>', methods=['GET'])
def get_store(store_id):
    """获取单个门店"""
    try:
        stores = read_stores()
        store = next((s for s in stores if s['id'] == store_id), None)

        if not store:
            return jsonify({'error': '门店不存在'}), 404

        return jsonify(store)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stores_bp.route('', methods=['POST'])
def create_store():
    """新增门店"""
    try:
        data = request.get_json()
        code = data.get('code')
        name = data.get('name')

        if not code or not name:
            return jsonify({'error': '门店编号和名称为必填项'}), 400

        stores = read_stores()

        # 检查门店编号是否已存在
        if any(s['code'] == code for s in stores):
            return jsonify({'error': '门店编号已存在'}), 400

        # 生成新的门店ID
        new_id = max([s['id'] for s in stores], default=0) + 1

        new_store = {
            'id': new_id,
            'code': code,
            'name': name,
            'status': data.get('status', 'active'),
            'remark': data.get('remark', ''),
            'color': data.get('color', '#ffffff'),
            'textColor': data.get('textColor', '#333333'),
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'updated_at': datetime.now().strftime('%Y-%m-%d')
        }

        stores.append(new_store)
        write_stores(stores)

        return jsonify({'success': True, 'store': new_store}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stores_bp.route('/<int:store_id>', methods=['PUT'])
def update_store(store_id):
    """更新门店"""
    try:
        data = request.get_json()
        stores = read_stores()

        store_index = next((i for i, s in enumerate(stores) if s['id'] == store_id), None)
        if store_index is None:
            return jsonify({'error': '门店不存在'}), 404

        store = stores[store_index]

        # 检查门店编号是否与其他门店重复
        code = data.get('code')
        if code and any(s['code'] == code and s['id'] != store_id for s in stores):
            return jsonify({'error': '门店编号已存在'}), 400

        # 更新门店信息
        if code:
            store['code'] = code
        if data.get('name'):
            store['name'] = data.get('name')
        if 'status' in data:
            store['status'] = data.get('status')
        if 'remark' in data:
            store['remark'] = data.get('remark')
        if 'color' in data:
            store['color'] = data.get('color')
        if 'textColor' in data:
            store['textColor'] = data.get('textColor')

        store['updated_at'] = datetime.now().strftime('%Y-%m-%d')

        write_stores(stores)
        return jsonify({'success': True, 'store': store})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stores_bp.route('/<int:store_id>', methods=['DELETE'])
def delete_store(store_id):
    """删除门店"""
    try:
        stores = read_stores()

        store_index = next((i for i, s in enumerate(stores) if s['id'] == store_id), None)
        if store_index is None:
            return jsonify({'error': '门店不存在'}), 404

        # TODO: 检查是否有关联的订单

        stores.pop(store_index)
        write_stores(stores)

        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
