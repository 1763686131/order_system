"""
商品和单位管理 API 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.db_helper import read_products, write_products

products_bp = Blueprint('products', __name__, url_prefix='/api/products')

# ==================== 单位管理 ====================

@products_bp.route('/units', methods=['GET'])
def get_units():
    """获取所有单位"""
    data = read_products()
    return jsonify(data.get('units', []))

@products_bp.route('/units', methods=['POST'])
def add_unit():
    """添加单位"""
    req_data = request.json
    data = read_products()
    units = data.get('units', [])

    unit_name = req_data.get('name', '').strip()
    if not unit_name:
        return jsonify({'success': False, 'message': '单位名称不能为空'}), 400

    # 检查是否已存在
    if any(u['name'] == unit_name for u in units):
        return jsonify({'success': False, 'message': '该单位已存在'}), 400

    new_unit = {
        'id': max([u['id'] for u in units], default=0) + 1,
        'name': unit_name,
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    units.append(new_unit)
    data['units'] = units
    write_products(data)

    return jsonify({'success': True, 'unit': new_unit})

@products_bp.route('/units/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    """删除单位"""
    data = read_products()
    units = data.get('units', [])

    data['units'] = [u for u in units if u['id'] != unit_id]
    write_products(data)

    return jsonify({'success': True, 'message': '删除成功'})

# ==================== 属性管理 ====================

@products_bp.route('/attributes', methods=['GET'])
def get_attributes():
    """获取所有属性"""
    data = read_products()
    return jsonify(data.get('attributes', []))

@products_bp.route('/attributes', methods=['POST'])
def add_attribute():
    """添加属性"""
    req_data = request.json
    data = read_products()
    attributes = data.get('attributes', [])

    attr_name = req_data.get('name', '').strip()
    if not attr_name:
        return jsonify({'success': False, 'message': '属性名称不能为空'}), 400

    # 检查是否已存在
    if any(a['name'] == attr_name for a in attributes):
        return jsonify({'success': False, 'message': '该属性已存在'}), 400

    new_attr = {
        'id': max([a['id'] for a in attributes], default=0) + 1,
        'name': attr_name,
        'options': [],
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    attributes.append(new_attr)
    data['attributes'] = attributes
    write_products(data)

    return jsonify({'success': True, 'attribute': new_attr})

@products_bp.route('/attributes/<int:attr_id>', methods=['PUT'])
def update_attribute(attr_id):
    """更新属性"""
    req_data = request.json
    data = read_products()
    attributes = data.get('attributes', [])

    for attr in attributes:
        if attr['id'] == attr_id:
            if 'name' in req_data:
                attr['name'] = req_data['name']
            if 'options' in req_data:
                attr['options'] = req_data['options']
            attr['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break

    data['attributes'] = attributes
    write_products(data)

    return jsonify({'success': True})

@products_bp.route('/attributes/<int:attr_id>', methods=['DELETE'])
def delete_attribute(attr_id):
    """删除属性"""
    data = read_products()
    attributes = data.get('attributes', [])

    data['attributes'] = [a for a in attributes if a['id'] != attr_id]
    write_products(data)

    return jsonify({'success': True, 'message': '删除成功'})

@products_bp.route('/attributes/<int:attr_id>/options', methods=['POST'])
def add_attribute_option(attr_id):
    """添加属性选项"""
    req_data = request.json
    data = read_products()
    attributes = data.get('attributes', [])

    option_name = req_data.get('name', '').strip()
    if not option_name:
        return jsonify({'success': False, 'message': '选项名称不能为空'}), 400

    for attr in attributes:
        if attr['id'] == attr_id:
            # 检查选项是否已存在
            if any(opt['name'] == option_name for opt in attr['options']):
                return jsonify({'success': False, 'message': '该选项已存在'}), 400

            new_option = {
                'id': max([opt['id'] for opt in attr['options']], default=attr_id * 100) + 1,
                'name': option_name
            }
            attr['options'].append(new_option)
            break

    data['attributes'] = attributes
    write_products(data)

    return jsonify({'success': True, 'option': new_option})

@products_bp.route('/attributes/<int:attr_id>/options/<int:option_id>', methods=['DELETE'])
def delete_attribute_option(attr_id, option_id):
    """删除属性选项"""
    data = read_products()
    attributes = data.get('attributes', [])

    for attr in attributes:
        if attr['id'] == attr_id:
            attr['options'] = [opt for opt in attr['options'] if opt['id'] != option_id]
            break

    data['attributes'] = attributes
    write_products(data)

    return jsonify({'success': True, 'message': '删除成功'})

# ==================== 商品管理 ====================

@products_bp.route('', methods=['GET'])
def get_products():
    """获取所有商品"""
    data = read_products()
    return jsonify(data.get('products', []))

@products_bp.route('', methods=['POST'])
def add_product():
    """添加商品"""
    req_data = request.json
    data = read_products()
    products = data.get('products', [])

    new_product = {
        'id': max([p['id'] for p in products], default=0) + 1,
        'code': req_data.get('code', ''),
        'name': req_data.get('name', ''),
        'specification': req_data.get('specification', ''),
        'category': req_data.get('categoryId', ''),
        'unitId': req_data.get('unitId'),
        'enableMultiUnit': req_data.get('enableMultiUnit', False),
        'notes': req_data.get('notes', ''),
        'enabled': req_data.get('enabled', True),
        'warehouseId': req_data.get('warehouseId'),
        'storeIds': req_data.get('storeIds', []),
        'warehouseCategories': req_data.get('warehouseCategories', {}),
        'unitConversions': req_data.get('unitConversions', []),
        'enableAttributes': req_data.get('enableAttributes', False),
        'attributeCombinations': req_data.get('attributeCombinations', []),
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    products.append(new_product)
    data['products'] = products
    write_products(data)

    return jsonify({'success': True, 'product': new_product})

@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """更新商品"""
    req_data = request.json
    data = read_products()
    products = data.get('products', [])

    for product in products:
        if product['id'] == product_id:
            product['code'] = req_data.get('code', '')
            product['name'] = req_data.get('name', '')
            product['specification'] = req_data.get('specification', '')
            product['category'] = req_data.get('categoryId', '')
            product['unitId'] = req_data.get('unitId')
            product['enableMultiUnit'] = req_data.get('enableMultiUnit', False)
            product['notes'] = req_data.get('notes', '')
            product['enabled'] = req_data.get('enabled', True)
            product['warehouseId'] = req_data.get('warehouseId')
            product['storeIds'] = req_data.get('storeIds', [])
            product['warehouseCategories'] = req_data.get('warehouseCategories', {})
            product['unitConversions'] = req_data.get('unitConversions', [])
            product['enableAttributes'] = req_data.get('enableAttributes', False)
            product['attributeCombinations'] = req_data.get('attributeCombinations', [])
            product['updatedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break

    data['products'] = products
    write_products(data)

    return jsonify({'success': True})

@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除商品"""
    data = read_products()
    products = data.get('products', [])

    data['products'] = [p for p in products if p['id'] != product_id]
    write_products(data)

    return jsonify({'success': True, 'message': '删除成功'})
