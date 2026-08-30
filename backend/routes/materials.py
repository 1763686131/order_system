"""
材料库存管理 API 路由
100%从旧代码移植
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.db_helper import read_materials, write_materials

materials_bp = Blueprint('materials', __name__, url_prefix='/api/materials')

@materials_bp.route('', methods=['GET'])
def get_materials():
    """获取材料库存信息"""
    return jsonify(read_materials())

@materials_bp.route('', methods=['POST'])
def add_material_record():
    """添加材料记录"""
    req_data = request.json
    mat_data = read_materials()
    records_list = mat_data.get('records', [])

    # 获取当前的词库，如果没有则给个空数组
    remark_tags = mat_data.get('remark_tags', [])

    ct = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_id = max([x['id'] for x in records_list], default=0) + 1

    # 提取前端传来的备注数据
    remark_text = str(req_data.get('remark', '')).strip()

    new_record = {
        "id": new_id,
        "used": float(req_data.get('used', 0)),
        "produced": float(req_data.get('produced', 0)),
        "date": ct,
        "remark": remark_text
    }
    records_list.append(new_record)
    mat_data['records'] = records_list

    # 🌟 核心逻辑：如果用户输入了备注，且这个词没有在词库中，则自动收录进去！
    if remark_text and remark_text not in remark_tags:
        remark_tags.append(remark_text)
        mat_data['remark_tags'] = remark_tags

    write_materials(mat_data)
    return jsonify({"success": True, "id": new_id})

@materials_bp.route('/stock', methods=['PUT'])
def update_stock():
    """更新库存"""
    req_data = request.json
    mat_data = read_materials()
    mat_data['stock'] = float(req_data.get('stock', 0))
    write_materials(mat_data)
    return jsonify({"success": True})

@materials_bp.route('/<int:record_id>', methods=['PUT'])
def update_material_record(record_id):
    """更新材料记录"""
    req_data = request.json
    mat_data = read_materials()
    for x in mat_data.get('records', []):
        if x['id'] == record_id:
            x['used'] = float(req_data.get('used', 0))
            x['produced'] = float(req_data.get('produced', 0))
            x['remark'] = str(req_data.get('remark', ''))
            break
    write_materials(mat_data)
    return jsonify({"success": True})

@materials_bp.route('/<int:record_id>', methods=['DELETE'])
def delete_material_record(record_id):
    """删除材料记录"""
    mat_data = read_materials()
    mat_data['records'] = [x for x in mat_data.get('records', []) if x['id'] != record_id]
    write_materials(mat_data)
    return jsonify({"success": True})
