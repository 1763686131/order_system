"""
打印模板路由模块
"""
from flask import Blueprint, request, jsonify
from utils.db import get_db
import json
from datetime import datetime

print_templates_bp = Blueprint('print_templates', __name__, url_prefix='/api/print-templates')


@print_templates_bp.route('', methods=['GET'])
def get_print_templates():
    """获取打印模板列表"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 获取查询参数
            business_type = request.args.get('businessType', '').strip()
            enabled_only = request.args.get('enabledOnly', 'false').lower() == 'true'

            # 构建查询
            query = "SELECT * FROM print_templates WHERE 1=1"
            params = []

            if business_type:
                query += " AND business_type = ?"
                params.append(business_type)

            if enabled_only:
                query += " AND enabled = 1"

            query += " ORDER BY is_default DESC, created_at DESC"

            cursor.execute(query, params)
            templates = [dict(row) for row in cursor.fetchall()]

            # 解析 content 字段（JSON）
            for template in templates:
                if template.get('content'):
                    try:
                        template['content'] = json.loads(template['content'])
                    except:
                        template['content'] = None

            return jsonify({
                'success': True,
                'data': templates
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@print_templates_bp.route('/<int:template_id>', methods=['GET'])
def get_print_template(template_id):
    """获取单个打印模板"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM print_templates WHERE id = ?", (template_id,))
            template = cursor.fetchone()

            if not template:
                return jsonify({'success': False, 'message': '模板不存在'}), 404

            template = dict(template)

            # 解析 content 字段
            if template.get('content'):
                try:
                    template['content'] = json.loads(template['content'])
                except:
                    template['content'] = None

            return jsonify({
                'success': True,
                'data': template
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@print_templates_bp.route('', methods=['POST'])
def create_print_template():
    """创建打印模板"""
    try:
        data = request.json

        # 验证必填字段
        required_fields = ['name', 'businessType', 'pageWidth', 'pageHeight']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400

        with get_db() as conn:
            cursor = conn.cursor()

            # 如果设置为默认模板，先取消同业务类型的其他默认模板
            if data.get('isDefault'):
                cursor.execute(
                    "UPDATE print_templates SET is_default = 0 WHERE business_type = ?",
                    (data['businessType'],)
                )

            # 序列化 content
            content_json = None
            if data.get('content'):
                content_json = json.dumps(data['content'], ensure_ascii=False)

            # 插入新模板
            cursor.execute('''
                INSERT INTO print_templates (
                    name, business_type, paper_type,
                    page_width, page_height, is_default,
                    enabled, content, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['businessType'],
                data.get('paperType', ''),
                data['pageWidth'],
                data['pageHeight'],
                1 if data.get('isDefault') else 0,
                1 if data.get('enabled', True) else 0,
                content_json,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

            template_id = cursor.lastrowid
            conn.commit()

            return jsonify({
                'success': True,
                'message': '创建成功',
                'data': {'id': template_id}
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@print_templates_bp.route('/<int:template_id>', methods=['PUT'])
def update_print_template(template_id):
    """更新打印模板"""
    try:
        data = request.json

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查模板是否存在
            cursor.execute("SELECT * FROM print_templates WHERE id = ?", (template_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '模板不存在'}), 404

            # 如果设置为默认模板，先取消同业务类型的其他默认模板
            if data.get('isDefault'):
                business_type = data.get('businessType')
                if not business_type:
                    # 获取当前模板的业务类型
                    cursor.execute("SELECT business_type FROM print_templates WHERE id = ?", (template_id,))
                    row = cursor.fetchone()
                    business_type = row['business_type'] if row else None

                if business_type:
                    cursor.execute(
                        "UPDATE print_templates SET is_default = 0 WHERE business_type = ? AND id != ?",
                        (business_type, template_id)
                    )

            # 序列化 content
            content_json = None
            if 'content' in data:
                if data['content']:
                    content_json = json.dumps(data['content'], ensure_ascii=False)

            # 构建更新语句
            update_fields = []
            params = []

            if 'name' in data:
                update_fields.append("name = ?")
                params.append(data['name'])

            if 'businessType' in data:
                update_fields.append("business_type = ?")
                params.append(data['businessType'])

            if 'paperType' in data:
                update_fields.append("paper_type = ?")
                params.append(data['paperType'])

            if 'pageWidth' in data:
                update_fields.append("page_width = ?")
                params.append(data['pageWidth'])

            if 'pageHeight' in data:
                update_fields.append("page_height = ?")
                params.append(data['pageHeight'])

            if 'isDefault' in data:
                update_fields.append("is_default = ?")
                params.append(1 if data['isDefault'] else 0)

            if 'enabled' in data:
                update_fields.append("enabled = ?")
                params.append(1 if data['enabled'] else 0)

            if 'content' in data:
                update_fields.append("content = ?")
                params.append(content_json)

            update_fields.append("updated_at = ?")
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            params.append(template_id)

            cursor.execute(
                f"UPDATE print_templates SET {', '.join(update_fields)} WHERE id = ?",
                params
            )

            conn.commit()

            return jsonify({
                'success': True,
                'message': '更新成功'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@print_templates_bp.route('/<int:template_id>', methods=['DELETE'])
def delete_print_template(template_id):
    """删除打印模板"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 检查是否是默认模板
            cursor.execute("SELECT is_default, business_type FROM print_templates WHERE id = ?", (template_id,))
            template = cursor.fetchone()

            if not template:
                return jsonify({'success': False, 'message': '模板不存在'}), 404

            if template['is_default']:
                return jsonify({'success': False, 'message': '不能删除默认模板，请先设置其他模板为默认'}), 400

            cursor.execute("DELETE FROM print_templates WHERE id = ?", (template_id,))
            conn.commit()

            return jsonify({
                'success': True,
                'message': '删除成功'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@print_templates_bp.route('/<int:template_id>/set-default', methods=['POST'])
def set_default_template(template_id):
    """设置默认模板"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 获取模板的业务类型
            cursor.execute("SELECT business_type FROM print_templates WHERE id = ?", (template_id,))
            template = cursor.fetchone()

            if not template:
                return jsonify({'success': False, 'message': '模板不存在'}), 404

            business_type = template['business_type']

            # 取消同业务类型的其他默认模板
            cursor.execute(
                "UPDATE print_templates SET is_default = 0 WHERE business_type = ?",
                (business_type,)
            )

            # 设置当前模板为默认
            cursor.execute(
                "UPDATE print_templates SET is_default = 1 WHERE id = ?",
                (template_id,)
            )

            conn.commit()

            return jsonify({
                'success': True,
                'message': '设置成功'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@print_templates_bp.route('/migrate', methods=['POST'])
def migrate_templates():
    """从 localStorage 迁移模板到数据库"""
    try:
        data = request.json
        templates = data.get('templates', [])

        if not templates or not isinstance(templates, list):
            return jsonify({'success': False, 'message': '无效的模板数据'}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            migrated_count = 0

            for template in templates:
                try:
                    # 检查是否已存在相同名称和业务类型的模板
                    cursor.execute(
                        "SELECT id FROM print_templates WHERE name = ? AND business_type = ?",
                        (template.get('name'), template.get('businessType'))
                    )
                    if cursor.fetchone():
                        continue  # 跳过已存在的模板

                    # 如果设置为默认模板，先取消同业务类型的其他默认模板
                    if template.get('isDefault'):
                        cursor.execute(
                            "UPDATE print_templates SET is_default = 0 WHERE business_type = ?",
                            (template.get('businessType'),)
                        )

                    # 序列化 content
                    content_json = None
                    if template.get('content'):
                        content_json = json.dumps(template['content'], ensure_ascii=False)

                    # 插入模板
                    cursor.execute('''
                        INSERT INTO print_templates (
                            name, business_type, paper_type,
                            page_width, page_height, is_default,
                            enabled, content, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        template.get('name'),
                        template.get('businessType'),
                        template.get('paperType', ''),
                        template.get('pageWidth'),
                        template.get('pageHeight'),
                        1 if template.get('isDefault') else 0,
                        1 if template.get('enabled', True) else 0,
                        content_json,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))

                    migrated_count += 1

                except Exception as e:
                    print(f"迁移模板失败: {template.get('name')}, 错误: {str(e)}")
                    continue

            conn.commit()

            return jsonify({
                'success': True,
                'message': f'成功迁移 {migrated_count} 个模板',
                'data': {'migratedCount': migrated_count}
            })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
