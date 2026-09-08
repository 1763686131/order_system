"""
原材料商品档案 API。

该接口与原材料使用记录 /api/materials 分开，避免两类数据互相影响。
"""
import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from utils.db import get_db


raw_material_products_bp = Blueprint(
    'raw_material_products',
    __name__,
    url_prefix='/api/raw-material-products',
)

JSON_FIELDS = {
    'store_ids': ('storeIds', []),
    'warehouse_categories': ('warehouseCategories', {}),
    'unit_conversions': ('unitConversions', []),
    'attribute_combinations': ('attributeCombinations', []),
}


def _decode_json(value, default):
    if not value:
        return default.copy()
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default.copy()


def _serialize_product(row):
    product = dict(row)
    for database_field, (response_field, default) in JSON_FIELDS.items():
        product[response_field] = _decode_json(
            product.pop(database_field, None),
            default,
        )

    product['unitId'] = product.pop('unit_id', None)
    product['enableMultiUnit'] = bool(product.pop('enable_multi_unit', 0))
    product['warehouseId'] = product.pop('warehouse_id', None)
    product['enableAttributes'] = bool(product.pop('enable_attributes', 0))
    product['enabled'] = bool(product.get('enabled', 1))
    product['createdAt'] = product.pop('created_at', None)
    product['updatedAt'] = product.pop('updated_at', None)
    return product


def _as_text(value):
    return '' if value is None else str(value).strip()


def _get_product(conn, product_id):
    row = conn.execute(
        'SELECT * FROM raw_material_products WHERE id = ?',
        (product_id,),
    ).fetchone()
    return _serialize_product(row) if row else None


def _payload_values(data):
    return (
        _as_text(data.get('code')),
        _as_text(data.get('name')),
        _as_text(data.get('specification')),
        data.get('categoryId', data.get('category')),
        data.get('unitId'),
        int(bool(data.get('enableMultiUnit', False))),
        _as_text(data.get('notes')),
        int(bool(data.get('enabled', True))),
        data.get('warehouseId'),
        json.dumps(data.get('storeIds', []), ensure_ascii=False),
        json.dumps(data.get('warehouseCategories', {}), ensure_ascii=False),
        json.dumps(data.get('unitConversions', []), ensure_ascii=False),
        int(bool(data.get('enableAttributes', False))),
        json.dumps(data.get('attributeCombinations', []), ensure_ascii=False),
    )


@raw_material_products_bp.route('', methods=['GET'])
def get_raw_material_products():
    """获取全部原材料商品档案。"""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM raw_material_products ORDER BY id DESC'
        ).fetchall()
        return jsonify([_serialize_product(row) for row in rows])


@raw_material_products_bp.route('', methods=['POST'])
def add_raw_material_product():
    """新增原材料商品档案。"""
    data = request.get_json(silent=True) or {}
    if not _as_text(data.get('name')):
        return jsonify({'success': False, 'message': '原材料名称不能为空'}), 400

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO raw_material_products (
                code, name, specification, category, unit_id,
                enable_multi_unit, notes, enabled, warehouse_id, store_ids,
                warehouse_categories, unit_conversions, enable_attributes,
                attribute_combinations, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*_payload_values(data), datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        )
        product = _get_product(conn, cursor.lastrowid)

    return jsonify({
        'success': True,
        'product': product,
        'rawMaterialProduct': product,
    })


@raw_material_products_bp.route('/<int:product_id>', methods=['PUT'])
def update_raw_material_product(product_id):
    """修改原材料商品档案。"""
    data = request.get_json(silent=True) or {}
    if not _as_text(data.get('name')):
        return jsonify({'success': False, 'message': '原材料名称不能为空'}), 400

    with get_db() as conn:
        exists = conn.execute(
            'SELECT 1 FROM raw_material_products WHERE id = ?',
            (product_id,),
        ).fetchone()
        if not exists:
            return jsonify({'success': False, 'message': '原材料不存在'}), 404

        conn.execute(
            """
            UPDATE raw_material_products SET
                code = ?, name = ?, specification = ?, category = ?,
                unit_id = ?, enable_multi_unit = ?, notes = ?, enabled = ?,
                warehouse_id = ?, store_ids = ?, warehouse_categories = ?,
                unit_conversions = ?, enable_attributes = ?,
                attribute_combinations = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                *_payload_values(data),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                product_id,
            ),
        )
        product = _get_product(conn, product_id)

    return jsonify({
        'success': True,
        'product': product,
        'rawMaterialProduct': product,
    })


@raw_material_products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_raw_material_product(product_id):
    """删除原材料商品档案。"""
    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM raw_material_products WHERE id = ?',
            (product_id,),
        )
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '原材料不存在'}), 404

    return jsonify({'success': True, 'message': '删除成功'})
