"""
数据库操作辅助函数
"""
import os
import json
from threading import Lock

# 文件锁
orders_lock = Lock()
users_lock = Lock()
materials_lock = Lock()
freight_records_lock = Lock()
warehouses_lock = Lock()
stores_lock = Lock()

# 数据库文件路径
USERS_FILE = '/app/data/users_db.json'
ORDERS_FILE = '/app/data/orders_db.json'
MATERIALS_FILE = '/app/data/material_db.json'
FREIGHT_RECORDS_FILE = '/app/data/freight_records_db.json'
STORES_FILE = '/app/data/stores_db.json'
WAREHOUSES_FILE = '/app/data/warehouses_db.json'

def read_users():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        d = [
            {"username": "1", "password": "741200", "role": "super_admin", "name": "系统超管"},
            {"username": "admin", "password": "admin123", "role": "admin", "name": "管理员"}
        ]
        write_users(d)
        return d
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_orders():
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    if not os.path.exists(ORDERS_FILE):
        from datetime import datetime
        ct = datetime.now().strftime('%Y-%m-%d %H:%M')
        d = {"orders": [{"id": 1, "title": "测试订单", "status": "pending", "type": 0, "date": ct, "completed_date": ""}]}
        write_orders(d)
        return d
    with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_orders(data):
    temp_file = ORDERS_FILE + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(temp_file, ORDERS_FILE)

def read_materials():
    os.makedirs(os.path.dirname(MATERIALS_FILE), exist_ok=True)
    if not os.path.exists(MATERIALS_FILE):
        d = {"total_stock": 5000.0, "records": [], "remark_tags": []}
        write_materials(d)
        return d
    with open(MATERIALS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_materials(data):
    with open(MATERIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_freight_records():
    with freight_records_lock:
        os.makedirs(os.path.dirname(FREIGHT_RECORDS_FILE), exist_ok=True)
        if not os.path.exists(FREIGHT_RECORDS_FILE):
            d = {"freight_records": [], "reserve_funds": []}
            write_freight_records(d)
            return d
        with open(FREIGHT_RECORDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def write_freight_records(data):
    with freight_records_lock:
        with open(FREIGHT_RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def read_stores():
    with stores_lock:
        os.makedirs(os.path.dirname(STORES_FILE), exist_ok=True)
        if not os.path.exists(STORES_FILE):
            d = []
            write_stores(d)
            return d
        with open(STORES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def write_stores(data):
    with stores_lock:
        with open(STORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def read_warehouses():
    with warehouses_lock:
        os.makedirs(os.path.dirname(WAREHOUSES_FILE), exist_ok=True)
        if not os.path.exists(WAREHOUSES_FILE):
            d = []
            write_warehouses(d)
            return d
        with open(WAREHOUSES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def write_warehouses(data):
    with warehouses_lock:
        with open(WAREHOUSES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
