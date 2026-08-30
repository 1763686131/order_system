"""
用户管理 API 路由
"""
from flask import Blueprint, request, jsonify
from utils.db_helper import read_users, write_users

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    req_data = request.json
    username = req_data.get('username')
    password = req_data.get('password')

    users = read_users()
    for user in users:
        if str(user['username']) == str(username) and user['password'] == password:
            return jsonify({
                "success": True,
                "username": user['username'],
                "name": user.get('name', user['username']),
                "role": user.get('role', 'employee')
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

@users_bp.route('/<username>', methods=['PUT'])
def update_user(username):
    """更新用户信息"""
    req_role = request.headers.get('Role')
    if req_role not in ['super_admin', 'admin']:
        return jsonify({"message": "权限不足"}), 403

    req_data = request.json
    users_data = read_users()

    for u in users_data:
        if str(u['username']) == str(username):
            target_role = req_data.get('role', u.get('role'))

            if req_role == 'admin' and target_role in ['super_admin', 'admin']:
                return jsonify({"message": "越权操作：管理员不能修改管理员/超管账号"}), 403

            u['name'] = req_data.get('name', u.get('name'))
            u['role'] = target_role

            if 'password' in req_data and req_data['password']:
                u['password'] = req_data['password']

            if 'permissions' in req_data:
                u['permissions'] = req_data['permissions']

            write_users(users_data)
            return jsonify({"success": True, "message": "用户更新成功"})

    return jsonify({"message": "用户不存在"}), 404

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
