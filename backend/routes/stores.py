"""
门店管理 API 路由
100%从旧代码移植
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.db_helper import read_stores, write_stores

stores_bp = Blueprint('stores', __name__, url_prefix='/api/stores')

@stores_bp.route('', methods=['GET'])
def get_stores():
    """获取所有门店"""
    stores = read_stores()
    return jsonify(stores)

@stores_bp.route('/<int:store_id>', methods=['GET'])
def get_store(store_id):
    """获取单个门店"""
    stores = read_stores()
    store = next((s for s in stores if s['id'] == store_id), None)
    if not store:
        return jsonify({'error': '门店不存在'}), 404
    return jsonify(store)

@stores_bp.route('', methods=['POST'])
def create_store():
    """创建门店"""
    req_data = request.json
    stores = read_stores()

    code = req_data.get('code', '').strip()
    name = req_data.get('name', '').strip()

    if not code or not name:
        return jsonify({'error': '门店编码和名称不能为空'}), 400

    # 检查编码是否重复
    if any(s['code'] == code for s in stores):
        return jsonify({'error': '门店编码已存在'}), 400

    new_id = max([s['id'] for s in stores], default=0) + 1

    new_store = {
        'id': new_id,
        'code': code,
        'name': name,
        'status': req_data.get('status', 'active'),
        'remark': req_data.get('remark', ''),
        'color': req_data.get('color', '#ffffff'),
        'textColor': req_data.get('textColor', '#333333'),
        'created_at': datetime.now().strftime('%Y-%m-%d'),
        'updated_at': datetime.now().strftime('%Y-%m-%d')
    }

    stores.append(new_store)
    write_stores(stores)

    return jsonify({'success': True, 'store': new_store})

@stores_bp.route('/<int:store_id>', methods=['PUT'])
def update_store(store_id):
    """更新门店"""
    req_data = request.json
    stores = read_stores()

    store_index = next((i for i, s in enumerate(stores) if s['id'] == store_id), None)
    if store_index is None:
        return jsonify({'error': '门店不存在'}), 404

    code = req_data.get('code', '').strip()
    if code and any(s['code'] == code and s['id'] != store_id for s in stores):
        return jsonify({'error': '门店编码已存在'}), 400

    stores[store_index]['code'] = code if code else stores[store_index]['code']
    stores[store_index]['name'] = req_data.get('name', stores[store_index]['name'])
    stores[store_index]['status'] = req_data.get('status', stores[store_index]['status'])
    stores[store_index]['color'] = req_data.get('color', stores[store_index]['color'])
    stores[store_index]['textColor'] = req_data.get('textColor', stores[store_index]['textColor'])
    stores[store_index]['remark'] = req_data.get('remark', '')
    stores[store_index]['updated_at'] = datetime.now().strftime('%Y-%m-%d')

    write_stores(stores)

    return jsonify({'success': True, 'store': stores[store_index]})

@stores_bp.route('/<int:store_id>', methods=['DELETE'])
def delete_store(store_id):
    """删除门店"""
    stores = read_stores()

    store_index = next((i for i, s in enumerate(stores) if s['id'] == store_id), None)
    if store_index is None:
        return jsonify({'error': '门店不存在'}), 404

    # TODO: 检查是否有关联的订单

    stores.pop(store_index)
    write_stores(stores)

    return jsonify({'success': True, 'message': '删除成功'})
