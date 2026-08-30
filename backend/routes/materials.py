"""
材料库存管理 API 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.db_helper import read_materials, write_materials, materials_lock

materials_bp = Blueprint('materials', __name__, url_prefix='/api/materials')

@materials_bp.route('', methods=['GET'])
def get_materials():
    """获取材料库存信息"""
    data = read_materials()
    return jsonify(data)

@materials_bp.route('/records', methods=['POST'])
def add_material_record():
    """添加材料记录"""
    with materials_lock:
        data = read_materials()
        records = data.get('records', [])

        req_data = request.json
        new_record = {
            'id': max([r.get('id', 0) for r in records], default=0) + 1,
            'date': req_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'type': req_data.get('type', 'in'),
            'quantity': float(req_data.get('quantity', 0)),
            'price': float(req_data.get('price', 0)),
            'supplier': req_data.get('supplier', ''),
            'remark': req_data.get('remark', ''),
            'creator': request.headers.get('Username', ''),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        records.append(new_record)

        # 更新总库存
        if new_record['type'] == 'in':
            data['total_stock'] = data.get('total_stock', 0) + new_record['quantity']
        else:
            data['total_stock'] = data.get('total_stock', 0) - new_record['quantity']

        data['records'] = records
        write_materials(data)

        return jsonify({'success': True, 'record': new_record})

@materials_bp.route('/records/<int:record_id>', methods=['PUT'])
def update_material_record(record_id):
    """更新材料记录"""
    with materials_lock:
        data = read_materials()
        records = data.get('records', [])

        target_record = next((r for r in records if r.get('id') == record_id), None)
        if not target_record:
            return jsonify({'error': '记录不存在'}), 404

        req_data = request.json
        old_quantity = target_record['quantity']
        old_type = target_record['type']

        # 更新记录
        target_record.update({
            'date': req_data.get('date', target_record.get('date')),
            'type': req_data.get('type', target_record.get('type')),
            'quantity': float(req_data.get('quantity', target_record.get('quantity'))),
            'price': float(req_data.get('price', target_record.get('price', 0))),
            'supplier': req_data.get('supplier', target_record.get('supplier', '')),
            'remark': req_data.get('remark', target_record.get('remark', ''))
        })

        # 重新计算库存
        if old_type == 'in':
            data['total_stock'] = data.get('total_stock', 0) - old_quantity
        else:
            data['total_stock'] = data.get('total_stock', 0) + old_quantity

        if target_record['type'] == 'in':
            data['total_stock'] = data.get('total_stock', 0) + target_record['quantity']
        else:
            data['total_stock'] = data.get('total_stock', 0) - target_record['quantity']

        write_materials(data)

        return jsonify({'success': True, 'record': target_record})

@materials_bp.route('/records/<int:record_id>', methods=['DELETE'])
def delete_material_record(record_id):
    """删除材料记录"""
    with materials_lock:
        data = read_materials()
        records = data.get('records', [])

        target_record = next((r for r in records if r.get('id') == record_id), None)
        if not target_record:
            return jsonify({'error': '记录不存在'}), 404

        # 恢复库存
        if target_record['type'] == 'in':
            data['total_stock'] = data.get('total_stock', 0) - target_record['quantity']
        else:
            data['total_stock'] = data.get('total_stock', 0) + target_record['quantity']

        records = [r for r in records if r.get('id') != record_id]
        data['records'] = records
        write_materials(data)

        return jsonify({'success': True, 'message': '删除成功'})

@materials_bp.route('/remark-tags', methods=['GET'])
def get_remark_tags():
    """获取备注标签"""
    data = read_materials()
    return jsonify(data.get('remark_tags', []))

@materials_bp.route('/remark-tags', methods=['POST'])
def add_remark_tag():
    """添加备注标签"""
    with materials_lock:
        data = read_materials()
        tags = data.get('remark_tags', [])

        req_data = request.json
        new_tag = (req_data.get('tag') or '').strip()

        if not new_tag:
            return jsonify({'success': False, 'message': '标签不能为空'}), 400

        if new_tag not in tags:
            tags.insert(0, new_tag)
            data['remark_tags'] = tags[:20]  # 只保留最近20个
            write_materials(data)

        return jsonify({'success': True, 'tags': tags})
