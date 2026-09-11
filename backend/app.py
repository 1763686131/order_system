"""
订单管理系统后端主入口文件
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import webbrowser
from threading import Timer

# 创建 Flask 应用
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Username", "Role"]}})

# 前端静态文件路径
if os.path.exists('/app/frontend/index.html'):
    FRONTEND_DIR = '/app/frontend'
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

FRONTEND_PATH = os.path.join(FRONTEND_DIR, 'index.html')

# ==========================================
# 导入并注册所有路由模块
# ==========================================
from routes.users import users_bp
from routes.orders import orders_bp
from routes.stores import stores_bp
from routes.warehouses import warehouses_bp
from routes.materials import materials_bp
from routes.freight import freight_bp
from routes.products import products_bp
from routes.raw_material_products import raw_material_products_bp
from routes.customers import customers_bp
from routes.hr_reports import hr_reports_bp
from routes.settings import settings_bp
from routes.stock_inbounds import stock_inbounds_bp
from routes.payment_receipts import payment_receipts_bp

app.register_blueprint(users_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(stores_bp)
app.register_blueprint(warehouses_bp)
app.register_blueprint(materials_bp)
app.register_blueprint(freight_bp)
app.register_blueprint(products_bp)
app.register_blueprint(raw_material_products_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(hr_reports_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(stock_inbounds_bp)
app.register_blueprint(payment_receipts_bp)

# ==========================================
# 健康检查接口
# ==========================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return {"status": "ok", "message": "服务运行正常"}

# ==========================================
# 运营商标签接口（独立路由）
# ==========================================
# 注意：这个接口已经在 orders_bp 中实现，这里保留是为了向后兼容
from utils.db_helper import read_carrier_tags, write_carrier_tags

@app.route('/api/carrier_tags', methods=['GET'])
def get_carrier_tags():
    tags = read_carrier_tags()
    return jsonify(tags)

@app.route('/api/carrier_tags', methods=['POST'])
def add_carrier_tag():
    data = request.json or {}
    new_tag = (data.get('tag') or '').strip()
    if not new_tag:
        return jsonify({'success': False, 'message': '标签不能为空'}), 400

    tags = read_carrier_tags()
    if new_tag not in tags:
        tags.insert(0, new_tag)
        write_carrier_tags(tags[:20])

    return jsonify({'success': True, 'tags': tags})

# ==========================================
# 登录接口别名（兼容旧版前端）
# ==========================================
from flask import request, jsonify
from utils.db_helper import read_users

@app.route('/api/login', methods=['POST'])
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
                "user": {
                    "username": user['username'],
                    "name": user.get('name', user['username']),
                    "role": user.get('role', 'employee'),
                    "permissions": user.get('permissions', [])
                }
            })

    return jsonify({"success": False, "message": "账号或密码错误"}), 401

# ==========================================
# 静态文件上传路径
# ==========================================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """访问上传的文件"""
    return send_from_directory('/app/uploads', filename)

# ==========================================
# 前端静态文件路由（必须放在最后）
# ==========================================
@app.route('/<path:path>')
def send_static_files(path):
    """前端路由拦截器"""
    # 如果是 API 请求，跳过（让 Flask 返回 404）
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404

    if '.' in path:
        return send_from_directory(FRONTEND_DIR, path)
    else:
        return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/')
def index():
    """首页"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

def open_browser():
    """自动打开浏览器"""
    if not os.path.exists('/app/frontend/index.html'):
        webbrowser.open("http://localhost:7899")

# ==========================================
# 主程序启动
# ==========================================
if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=7899, debug=False)
