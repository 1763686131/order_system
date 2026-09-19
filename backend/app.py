"""
订单管理系统后端主入口文件
"""
from datetime import timedelta
from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import secrets
import webbrowser
from threading import Timer


def _load_secret_key():
    configured_key = str(os.environ.get("APP_SECRET_KEY") or "").strip()
    if configured_key:
        return configured_key

    if os.path.isdir("/app/data"):
        secret_path = "/app/data/.app_secret_key"
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        secret_path = os.path.join(project_root, "data", ".app_secret_key")

    os.makedirs(os.path.dirname(secret_path), exist_ok=True)
    try:
        with open(secret_path, "r", encoding="utf-8") as secret_file:
            persisted_key = secret_file.read().strip()
            if persisted_key:
                return persisted_key
    except FileNotFoundError:
        pass

    generated_key = secrets.token_hex(32)
    try:
        descriptor = os.open(
            secret_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as secret_file:
            secret_file.write(generated_key)
        return generated_key
    except FileExistsError:
        with open(secret_path, "r", encoding="utf-8") as secret_file:
            return secret_file.read().strip() or generated_key


# 创建 Flask 应用
app = Flask(__name__)
app.config.update(
    SECRET_KEY=_load_secret_key(),
    PERMANENT_SESSION_LIFETIME=timedelta(days=365),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
)
cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": cors_origins,
            "allow_headers": ["Content-Type"],
        }
    },
    supports_credentials=True,
)

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
from routes.auth import auth_bp
from routes.access import access_bp
from routes.employees import employees_bp
from routes.departments import departments_bp
from routes.directory import directory_bp
from routes.orders import orders_bp
from routes.stores import stores_bp
from routes.warehouses import warehouses_bp
from routes.freight import freight_bp
from routes.products import products_bp
from routes.raw_material_products import raw_material_products_bp
from routes.customers import customers_bp
from routes.hr_reports import hr_reports_bp
from routes.settings import settings_bp
from routes.stock_inbounds import stock_inbounds_bp
from routes.material_outbounds import material_outbounds_bp
from routes.payment_receipts import payment_receipts_bp
from routes.returns import returns_bp
from routes.bank_accounts import bank_accounts_bp, upload_bp as bank_account_upload_bp
from routes.print_templates import print_templates_bp

app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(access_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(departments_bp)
app.register_blueprint(directory_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(stores_bp)
app.register_blueprint(warehouses_bp)
app.register_blueprint(freight_bp)
app.register_blueprint(products_bp)
app.register_blueprint(raw_material_products_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(hr_reports_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(stock_inbounds_bp)
app.register_blueprint(material_outbounds_bp)
app.register_blueprint(payment_receipts_bp)
app.register_blueprint(returns_bp)
app.register_blueprint(bank_accounts_bp)
app.register_blueprint(bank_account_upload_bp)
app.register_blueprint(print_templates_bp)

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

from flask import request, jsonify

# ==========================================
# 静态文件上传路径
# ==========================================
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """访问上传的文件"""
    # 银行卡图片目录可在系统设置中修改；其它历史上传仍使用默认 uploads 根目录。
    if filename.startswith('bank-cards/backgrounds/'):
        from utils.system_settings import DEFAULT_BANK_CARD_BG_PATH, get_setting, normalize_server_path
        root = normalize_server_path(
            get_setting('bank_cards.bg_path', DEFAULT_BANK_CARD_BG_PATH)
            or DEFAULT_BANK_CARD_BG_PATH
        )
        return send_from_directory(root, filename.removeprefix('bank-cards/backgrounds/'))
    if filename.startswith('bank-cards/icons/'):
        from utils.system_settings import DEFAULT_BANK_ICON_PATH, get_setting, normalize_server_path
        root = normalize_server_path(
            get_setting('bank_cards.icon_path', DEFAULT_BANK_ICON_PATH)
            or DEFAULT_BANK_ICON_PATH
        )
        return send_from_directory(root, filename.removeprefix('bank-cards/icons/'))

    upload_root = '/app/uploads'
    if not os.path.isdir(upload_root):
        upload_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    return send_from_directory(upload_root, filename)

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
