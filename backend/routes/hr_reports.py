"""
人事检测报告 API 路由
支持文件上传、同步扫描、分享功能
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from utils.db import get_db
import mimetypes

hr_reports_bp = Blueprint('hr_reports', __name__, url_prefix='/api/hr/reports')

# 文件存储路径配置
if os.path.exists('/app/frontend/index.html') and os.path.isdir('/app/uploads'):
    UPLOAD_BASE_PATH = '/app/uploads/hr_reports'
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_BASE_PATH = os.path.join(BASE_DIR, 'uploads', 'hr_reports')

# 确保上传目录存在
os.makedirs(UPLOAD_BASE_PATH, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls': 'application/vnd.ms-excel',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

def get_file_hash(filepath):
    """计算文件MD5哈希"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def get_file_type(filename):
    """根据文件名获取文件类型"""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext == 'pdf':
        return 'pdf'
    elif ext in ['jpg', 'jpeg', 'png', 'gif']:
        return 'image'
    elif ext in ['xlsx', 'xls']:
        return 'excel'
    elif ext in ['doc', 'docx']:
        return 'word'
    else:
        return 'other'

@hr_reports_bp.route('/sync', methods=['POST'])
def sync_files():
    """
    扫描文件夹并同步到数据库
    支持多级文件夹结构
    """
    try:
        # 递归扫描文件夹
        scanned_files = []
        new_count = 0
        updated_count = 0

        def scan_directory(dir_path, relative_path=''):
            """递归扫描目录"""
            if not os.path.exists(dir_path):
                return

            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                item_relative = os.path.join(relative_path, item) if relative_path else item

                if os.path.isdir(item_path):
                    # 递归扫描子文件夹
                    scan_directory(item_path, item_relative)
                elif os.path.isfile(item_path):
                    # 检查文件扩展名
                    ext = item.rsplit('.', 1)[-1].lower() if '.' in item else ''
                    if ext in ALLOWED_EXTENSIONS:
                        scanned_files.append({
                            'filename': item,
                            'filepath': item_relative.replace('\\', '/'),
                            'fullpath': item_path,
                            'size': os.path.getsize(item_path),
                            'modified_time': datetime.fromtimestamp(os.path.getmtime(item_path))
                        })

        # 开始扫描
        scan_directory(UPLOAD_BASE_PATH)

        with get_db() as conn:
            cursor = conn.cursor()

            # 获取数据库中已有的文件（按文件路径）
            cursor.execute('SELECT id, file_path, file_hash FROM hr_reports')
            existing_files = {row['file_path']: {'id': row['id'], 'hash': row['file_hash']}
                            for row in cursor.fetchall()}

            scanned_paths = set()

            # 处理扫描到的文件
            for file_info in scanned_files:
                filepath = file_info['filepath']
                scanned_paths.add(filepath)

                # 计算文件哈希
                file_hash = get_file_hash(file_info['fullpath'])
                file_type = get_file_type(file_info['filename'])

                if filepath in existing_files:
                    # 文件已存在，检查是否有变化
                    if existing_files[filepath]['hash'] != file_hash:
                        # 文件已修改，更新记录
                        cursor.execute('''
                            UPDATE hr_reports
                            SET file_hash = ?,
                                file_size = ?,
                                file_type = ?,
                                updated_at = ?
                            WHERE file_path = ?
                        ''', (file_hash, file_info['size'], file_type,
                              datetime.now(), filepath))
                        updated_count += 1
                else:
                    # 新文件，插入记录
                    file_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO hr_reports (
                            id, filename, file_path, file_hash, file_size,
                            file_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (file_id, file_info['filename'], filepath, file_hash,
                          file_info['size'], file_type,
                          file_info['modified_time'], datetime.now()))
                    new_count += 1

            # 删除数据库中已不存在的文件记录
            deleted_count = 0
            for db_path in existing_files:
                if db_path not in scanned_paths:
                    cursor.execute('DELETE FROM hr_reports WHERE file_path = ?', (db_path,))
                    deleted_count += 1

            conn.commit()

        return jsonify({
            'success': True,
            'message': f'同步完成: 新增 {new_count} 个，更新 {updated_count} 个，删除 {deleted_count} 个',
            'stats': {
                'new': new_count,
                'updated': updated_count,
                'deleted': deleted_count,
                'total': len(scanned_files)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500

@hr_reports_bp.route('/list', methods=['GET'])
def get_files_list():
    """
    获取文件列表（树形结构）
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, filename, file_path, file_size, file_type,
                       created_at, updated_at
                FROM hr_reports
                ORDER BY file_path
            ''')
            rows = cursor.fetchall()

        # 构建树形结构
        tree = {}

        for row in rows:
            path_parts = row['file_path'].split('/')
            current = tree

            # 遍历路径，构建文件夹层级
            for i, part in enumerate(path_parts[:-1]):
                if part not in current:
                    current[part] = {'_folders': {}, '_files': []}
                current = current[part]['_folders']

            # 添加文件到最后一级
            filename = path_parts[-1]
            if '_files' not in current:
                current['_files'] = []

            current['_files'].append({
                'id': row['id'],
                'name': row['filename'],
                'path': row['file_path'],
                'size': row['file_size'],
                'type': row['file_type'],
                'createdAt': row['created_at'],
                'updatedAt': row['updated_at']
            })

        def build_tree(node, path=''):
            """递归构建树形结构"""
            result = {'folders': [], 'files': []}

            for folder_name, folder_data in node.items():
                if folder_name == '_files':
                    result['files'] = folder_data
                elif folder_name == '_folders':
                    continue
                else:
                    folder_path = f"{path}/{folder_name}" if path else folder_name
                    subtree = build_tree(folder_data['_folders'], folder_path)
                    result['folders'].append({
                        'name': folder_name,
                        'path': folder_path,
                        'folders': subtree['folders'],
                        'files': subtree['files']
                    })

            return result

        result = build_tree(tree)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取列表失败: {str(e)}'
        }), 500

@hr_reports_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    上传文件
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'}), 400

        file = request.files['file']
        folder_path = request.form.get('folder_path', '')

        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400

        # 检查文件类型
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'success': False, 'message': '不支持的文件类型'}), 400

        # 安全的文件名
        filename = secure_filename(file.filename)

        # 构建保存路径
        if folder_path:
            save_dir = os.path.join(UPLOAD_BASE_PATH, folder_path)
        else:
            save_dir = UPLOAD_BASE_PATH

        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        # 保存文件
        file.save(save_path)

        # 计算文件信息
        file_size = os.path.getsize(save_path)
        file_hash = get_file_hash(save_path)
        file_type = get_file_type(filename)
        relative_path = os.path.join(folder_path, filename).replace('\\', '/') if folder_path else filename

        # 写入数据库
        with get_db() as conn:
            cursor = conn.cursor()
            file_id = str(uuid.uuid4())

            cursor.execute('''
                INSERT INTO hr_reports (
                    id, filename, file_path, file_hash, file_size,
                    file_type, uploader, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_id, filename, relative_path, file_hash, file_size,
                  file_type, request.headers.get('Username', 'unknown'),
                  datetime.now(), datetime.now()))

            conn.commit()

        return jsonify({
            'success': True,
            'message': '上传成功',
            'file': {
                'id': file_id,
                'name': filename,
                'path': relative_path,
                'size': file_size,
                'type': file_type
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500

@hr_reports_bp.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """
    下载或预览文件
    - PDF/图片：在浏览器中预览
    - 其他文件：下载
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT filename, file_path, file_type
                FROM hr_reports
                WHERE id = ?
            ''', (file_id,))
            row = cursor.fetchone()

        if not row:
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        file_path = os.path.join(UPLOAD_BASE_PATH, row['file_path'])

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件已丢失'}), 404

        # PDF 和图片在浏览器中预览，其他文件下载
        if row['file_type'] in ['pdf', 'image']:
            return send_file(
                file_path,
                mimetype=mimetypes.guess_type(row['filename'])[0],
                as_attachment=False,
                download_name=row['filename']
            )
        else:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=row['filename']
            )

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载失败: {str(e)}'
        }), 500

@hr_reports_bp.route('/share/<file_id>', methods=['POST'])
def create_share_link(file_id):
    """
    创建分享链接
    """
    try:
        req_data = request.json or {}
        expire_days = req_data.get('expire_days', 7)  # 默认7天过期

        with get_db() as conn:
            cursor = conn.cursor()

            # 检查文件是否存在
            cursor.execute('SELECT id FROM hr_reports WHERE id = ?', (file_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '文件不存在'}), 404

            # 生成分享token
            share_token = str(uuid.uuid4())
            expire_at = datetime.now() + timedelta(days=expire_days)

            # 格式化为标准字符串（不带毫秒）
            expire_at_str = expire_at.strftime('%Y-%m-%d %H:%M:%S')

            # 更新分享信息
            cursor.execute('''
                UPDATE hr_reports
                SET share_token = ?, share_expire = ?
                WHERE id = ?
            ''', (share_token, expire_at_str, file_id))

            conn.commit()

        return jsonify({
            'success': True,
            'share_token': share_token,
            'expire_at': expire_at_str
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建分享失败: {str(e)}'
        }), 500

@hr_reports_bp.route('/share/<share_token>', methods=['GET'])
def download_shared_file(share_token):
    """
    通过分享链接下载/预览文件
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, filename, file_path, share_expire, file_type
                FROM hr_reports
                WHERE share_token = ?
            ''', (share_token,))
            row = cursor.fetchone()

        if not row:
            return jsonify({'success': False, 'message': '分享链接无效'}), 404

        # 检查是否过期
        if row['share_expire']:
            try:
                # 尝试多种日期格式
                expire_str = str(row['share_expire']).strip()

                # 尝试标准格式
                try:
                    expire_time = datetime.strptime(expire_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # 尝试带毫秒格式
                    try:
                        expire_time = datetime.strptime(expire_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # ISO格式
                        expire_time = datetime.fromisoformat(expire_str.replace('T', ' ').split('.')[0])

                if datetime.now() > expire_time:
                    return jsonify({'success': False, 'message': '分享链接已过期'}), 403
            except Exception as e:
                # 如果日期解析失败，记录错误但不阻止访问
                print(f"日期解析错误: {e}, 原始值: {row['share_expire']}")

        file_path = os.path.join(UPLOAD_BASE_PATH, row['file_path'])

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件已丢失'}), 404

        # PDF 和图片在浏览器中预览，其他文件下载
        if row['file_type'] in ['pdf', 'image']:
            return send_file(
                file_path,
                mimetype=mimetypes.guess_type(row['filename'])[0],
                as_attachment=False,
                download_name=row['filename']
            )
        else:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=row['filename']
            )

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载失败: {str(e)}'
        }), 500

@hr_reports_bp.route('/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    删除文件（删除数据库记录和物理文件）
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM hr_reports WHERE id = ?', (file_id,))
            row = cursor.fetchone()

            if not row:
                return jsonify({'success': False, 'message': '文件不存在'}), 404

            # 删除物理文件
            file_path = os.path.join(UPLOAD_BASE_PATH, row['file_path'])
            if os.path.exists(file_path):
                os.remove(file_path)

            # 删除数据库记录
            cursor.execute('DELETE FROM hr_reports WHERE id = ?', (file_id,))
            conn.commit()

        return jsonify({'success': True, 'message': '删除成功'})

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@hr_reports_bp.route('/folder/rename', methods=['POST'])
def rename_folder():
    """
    重命名文件夹（同时更新数据库中所有相关文件的路径）
    """
    try:
        req_data = request.json or {}
        old_path = req_data.get('old_path', '')
        new_name = req_data.get('new_name', '')

        if not old_path or not new_name:
            return jsonify({'success': False, 'message': '参数不完整'}), 400

        # 构建新旧路径
        old_full_path = os.path.join(UPLOAD_BASE_PATH, old_path)

        # 获取父目录和新路径
        parent_dir = os.path.dirname(old_full_path)
        new_full_path = os.path.join(parent_dir, new_name)

        if not os.path.exists(old_full_path):
            return jsonify({'success': False, 'message': '文件夹不存在'}), 404

        if os.path.exists(new_full_path):
            return jsonify({'success': False, 'message': '目标文件夹已存在'}), 400

        # 重命名物理文件夹
        os.rename(old_full_path, new_full_path)

        # 更新数据库中所有相关文件的路径
        with get_db() as conn:
            cursor = conn.cursor()

            # 查询所有以旧路径开头的文件
            cursor.execute('''
                SELECT id, file_path FROM hr_reports
                WHERE file_path LIKE ?
            ''', (old_path + '%',))

            files = cursor.fetchall()

            # 构建新的相对路径前缀
            parent_relative = os.path.dirname(old_path)
            new_relative_prefix = os.path.join(parent_relative, new_name).replace('\\', '/') if parent_relative else new_name

            # 更新每个文件的路径
            for file in files:
                old_file_path = file['file_path']
                # 替换路径前缀
                new_file_path = old_file_path.replace(old_path, new_relative_prefix, 1)

                cursor.execute('''
                    UPDATE hr_reports
                    SET file_path = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_file_path, datetime.now(), file['id']))

            conn.commit()

        return jsonify({'success': True, 'message': '重命名成功'})

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'重命名失败: {str(e)}'
        }), 500


@hr_reports_bp.route('/folder/delete', methods=['DELETE'])
def delete_folder():
    """
    删除文件夹（删除物理文件夹及数据库中所有相关记录）
    """
    try:
        req_data = request.json or {}
        folder_path = req_data.get('folder_path', '')

        if not folder_path:
            return jsonify({'success': False, 'message': '参数不完整'}), 400

        full_path = os.path.join(UPLOAD_BASE_PATH, folder_path)

        if not os.path.exists(full_path):
            return jsonify({'success': False, 'message': '文件夹不存在'}), 404

        # 删除物理文件夹及其内容
        import shutil
        shutil.rmtree(full_path)

        # 删除数据库中所有相关记录
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM hr_reports
                WHERE file_path LIKE ?
            ''', (folder_path + '%',))
            deleted_count = cursor.rowcount
            conn.commit()

        return jsonify({
            'success': True,
            'message': f'删除成功，共删除 {deleted_count} 个文件'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@hr_reports_bp.route('/move', methods=['POST'])
def move_file():
    """
    移动文件到另一个文件夹
    """
    try:
        req_data = request.json or {}
        file_id = req_data.get('file_id', '')
        target_folder = req_data.get('target_folder', '')  # 目标文件夹相对路径

        if not file_id:
            return jsonify({'success': False, 'message': '参数不完整'}), 400

        with get_db() as conn:
            cursor = conn.cursor()

            # 获取原文件信息
            cursor.execute('SELECT filename, file_path FROM hr_reports WHERE id = ?', (file_id,))
            row = cursor.fetchone()

            if not row:
                return jsonify({'success': False, 'message': '文件不存在'}), 404

            old_file_path = os.path.join(UPLOAD_BASE_PATH, row['file_path'])

            # 构建新路径
            if target_folder:
                new_relative_path = os.path.join(target_folder, row['filename']).replace('\\', '/')
                new_file_path = os.path.join(UPLOAD_BASE_PATH, target_folder, row['filename'])
                target_dir = os.path.join(UPLOAD_BASE_PATH, target_folder)
            else:
                new_relative_path = row['filename']
                new_file_path = os.path.join(UPLOAD_BASE_PATH, row['filename'])
                target_dir = UPLOAD_BASE_PATH

            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)

            # 检查目标文件是否已存在
            if os.path.exists(new_file_path):
                return jsonify({'success': False, 'message': '目标位置已存在同名文件'}), 400

            # 移动物理文件
            import shutil
            shutil.move(old_file_path, new_file_path)

            # 更新数据库
            cursor.execute('''
                UPDATE hr_reports
                SET file_path = ?, updated_at = ?
                WHERE id = ?
            ''', (new_relative_path, datetime.now(), file_id))

            conn.commit()

        return jsonify({'success': True, 'message': '移动成功'})

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'移动失败: {str(e)}'
        }), 500
