"""
仓库管理 API 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.db_helper import read_warehouses, write_warehouses

warehouses_bp = Blueprint('warehouses', __name__, url_prefix='/api/warehouses')

@warehouses_bp.route('', methods=['GET'])
def get_warehouses():
    """获取所有仓库列表"""
    try:
        store_id = request.args.get('storeId')
        warehouses = read_warehouses()

        # 如果指定了门店ID，只返回该门店的仓库
        if store_id:
            warehouses = [w for w in warehouses if w.get('storeId') == int(store_id)]

        return jsonify(warehouses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>', methods=['GET'])
def get_warehouse(warehouse_id):
    """获取单个仓库详情"""
    try:
        warehouses = read_warehouses()
        warehouse = next((w for w in warehouses if w['id'] == warehouse_id), None)

        if not warehouse:
            return jsonify({'error': '仓库不存在'}), 404

        return jsonify(warehouse)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@warehouses_bp.route('', methods=['POST'])
def create_warehouse():
    """新增仓库"""
    try:
        data = request.get_json()
        code = data.get('code')
        name = data.get('name')
        store_id = data.get('storeId')
        remark = data.get('remark', '')

        if not code or not name or not store_id:
            return jsonify({'error': '仓库ID、名称和门店ID为必填项'}), 400

        warehouses = read_warehouses()

        # 检查仓库编号是否已存在
        if any(w['code'] == code for w in warehouses):
            return jsonify({'error': '仓库ID已存在'}), 400

        # 生成新的仓库ID
        new_id = max([w['id'] for w in warehouses], default=0) + 1

        new_warehouse = {
            'id': new_id,
            'code': code,
            'name': name,
            'storeId': int(store_id),
            'remark': remark,
            'status': 'active',
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'updated_at': datetime.now().strftime('%Y-%m-%d'),
            'categories': []
        }

        warehouses.append(new_warehouse)
        write_warehouses(warehouses)

        return jsonify(new_warehouse), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>', methods=['PUT'])
def update_warehouse(warehouse_id):
    """修改仓库"""
    try:
        data = request.get_json()
        warehouses = read_warehouses()

        warehouse = next((w for w in warehouses if w['id'] == warehouse_id), None)
        if not warehouse:
            return jsonify({'error': '仓库不存在'}), 404

        # 检查仓库编号是否与其他仓库重复
        code = data.get('code')
        if code and any(w['code'] == code and w['id'] != warehouse_id for w in warehouses):
            return jsonify({'error': '仓库ID已存在'}), 400

        # 更新仓库信息
        if code:
            warehouse['code'] = code
        if data.get('name'):
            warehouse['name'] = data.get('name')
        if data.get('storeId'):
            warehouse['storeId'] = int(data.get('storeId'))
        if 'remark' in data:
            warehouse['remark'] = data.get('remark')
        if data.get('status'):
            warehouse['status'] = data.get('status')

        warehouse['updated_at'] = datetime.now().strftime('%Y-%m-%d')

        write_warehouses(warehouses)
        return jsonify(warehouse)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>', methods=['DELETE'])
def delete_warehouse(warehouse_id):
    """删除仓库"""
    try:
        warehouses = read_warehouses()
        warehouse_index = next((i for i, w in enumerate(warehouses) if w['id'] == warehouse_id), None)

        if warehouse_index is None:
            return jsonify({'error': '仓库不存在'}), 404

        warehouses.pop(warehouse_index)
        write_warehouses(warehouses)

        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>/categories', methods=['POST'])
def create_category(warehouse_id):
    """新增仓库分类"""
    try:
        data = request.get_json()
        name = data.get('name')
        code = data.get('code')

        if not name:
            return jsonify({'error': '分类名称为必填项'}), 400

        warehouses = read_warehouses()
        warehouse = next((w for w in warehouses if w['id'] == warehouse_id), None)

        if not warehouse:
            return jsonify({'error': '仓库不存在'}), 404

        # 生成新的分类ID
        categories = warehouse.get('categories', [])
        new_id = max([c['id'] for c in categories], default=warehouse_id * 100) + 1

        new_category = {
            'id': new_id,
            'name': name,
            'code': code if code else f'CAT{new_id}',
            'created_at': datetime.now().strftime('%Y-%m-%d')
        }

        categories.append(new_category)
        warehouse['categories'] = categories
        warehouse['updated_at'] = datetime.now().strftime('%Y-%m-%d')

        write_warehouses(warehouses)
        return jsonify(new_category), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>/categories/<int:category_id>', methods=['PUT'])
def update_category(warehouse_id, category_id):
    """修改仓库分类"""
    try:
        data = request.get_json()
        warehouses = read_warehouses()
        warehouse = next((w for w in warehouses if w['id'] == warehouse_id), None)

        if not warehouse:
            return jsonify({'error': '仓库不存在'}), 404

        category = next((c for c in warehouse.get('categories', []) if c['id'] == category_id), None)
        if not category:
            return jsonify({'error': '分类不存在'}), 404

        if data.get('name'):
            category['name'] = data.get('name')
        if data.get('code'):
            category['code'] = data.get('code')

        warehouse['updated_at'] = datetime.now().strftime('%Y-%m-%d')

        write_warehouses(warehouses)
        return jsonify(category)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@warehouses_bp.route('/<int:warehouse_id>/categories/<int:category_id>', methods=['DELETE'])
def delete_category(warehouse_id, category_id):
    """删除仓库分类"""
    try:
        warehouses = read_warehouses()
        warehouse = next((w for w in warehouses if w['id'] == warehouse_id), None)

        if not warehouse:
            return jsonify({'error': '仓库不存在'}), 404

        categories = warehouse.get('categories', [])
        category_index = next((i for i, c in enumerate(categories) if c['id'] == category_id), None)

        if category_index is None:
            return jsonify({'error': '分类不存在'}), 404

        categories.pop(category_index)
        warehouse['categories'] = categories
        warehouse['updated_at'] = datetime.now().strftime('%Y-%m-%d')

        write_warehouses(warehouses)
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
