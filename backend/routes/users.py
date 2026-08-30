"""
用户管理 API 路由
100%从旧代码移植
"""
from flask import Blueprint, request, jsonify
from utils.db_helper import read_users, write_users

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    req_data = request.json
    users_data = read_users()
    for u in users_data:
        if str(u['username']) == str(req_data.get('username')) and u['password'] == req_data.get('password'):
            return jsonify({
                "success": True,
                "user": {
                    "username": u['username'],
                    "name": u.get('name', u['username']),
                    "role": u['role'],
                    "permissions": u.get('permissions', [])
                }
            })
    return jsonify({"success": False, "message": "账号或密码错误"}), 401

@users_bp.route('', methods=['GET'])
def get_all_users():
    """获取所有用户"""
    return jsonify(read_users())

@users_bp.route('', methods=['POST'])
def add_user():
    """新增用户"""
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']:
        return jsonify({"message": "权限不足"}), 403

    req_data = request.json
    users_data = read_users()
    target_role = req_data.get('role', 'employee')

    if req_role == 'admin' and target_role in ['super_admin', 'admin']:
        return jsonify({"message": "越权操作：管理员只能创建员工账号"}), 403

    for u in users_data:
        if str(u['username']) == str(req_data.get('username')):
            return jsonify({"message": "账号已存在"}), 400

    users_data.append({
        "username": req_data.get('username'),
        "name": req_data.get('name', req_data.get('username')),
        "password": req_data.get('password'),
        "role": target_role,
        "permissions": req_data.get('permissions', [])
    })

    write_users(users_data)
    return jsonify({"success": True, "message": "用户创建成功"})

@users_bp.route('/<username>', methods=['DELETE'])
def delete_user(username):
    """删除用户"""
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']:
        return jsonify({"message": "权限不足"}), 403

    users_data = read_users()

    for u in users_data:
        if str(u['username']) == str(username):
            if u.get('role') in ['super_admin', 'admin'] and req_role == 'admin':
                return jsonify({"message": "越权操作：管理员不能删除管理员/超管账号"}), 403

            users_data.remove(u)
            write_users(users_data)
            return jsonify({"success": True, "message": "用户删除成功"})

    return jsonify({"message": "用户不存在"}), 404

@users_bp.route('/<username>/password', methods=['PUT'])
def update_user_password(username):
    """更新用户密码"""
    if request.headers.get('Role') not in ['super_admin', 'admin']:
        return jsonify({"message": "权限不足"}), 403
    req_data = request.json
    users_data = read_users()
    for u in users_data:
        if str(u['username']) == str(username):
            u['password'] = req_data.get('password')
            break
    write_users(users_data)
    return jsonify({"success": True})

@users_bp.route('/<username>/permissions', methods=['PUT'])
def update_user_permissions(username):
    """更新用户权限"""
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']:
        return jsonify({"message": "权限不足"}), 403

    req_data = request.json
    perms = req_data.get('permissions', [])
    new_role = req_data.get('role')
    new_name = req_data.get('name')
    new_created_at = req_data.get('createdAt')  # 新增：支持修改创建时间

    users_data = read_users()
    for u in users_data:
        if str(u['username']) == str(username):
            if req_role == 'admin' and u['role'] in ['super_admin', 'admin']:
                return jsonify({"message": "越权：无权修改高级别账户"}), 403

            if req_role == 'admin':
                admin_restricted = ['pending.edit', 'pending.delete', 'completed.delete', 'material.edit', 'material.edit_stock', 'material.delete']
                old_perms = set(u.get('permissions', []))
                new_perms = set(perms)
                for restricted in admin_restricted:
                    if restricted in old_perms:
                        new_perms.add(restricted)
                    else:
                        new_perms.discard(restricted)
                perms = list(new_perms)

            u['permissions'] = perms
            if new_name is not None:
                u['name'] = new_name

            # 新增：支持修改创建时间
            if new_created_at is not None:
                u['createdAt'] = new_created_at

            if new_role and req_role == 'super_admin' and u['role'] != 'super_admin':
                u['role'] = new_role
            break

    write_users(users_data)
    return jsonify({"success": True})
