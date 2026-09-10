from datetime import datetime
from math import isfinite

from flask import Blueprint, jsonify, request

from utils.db import get_db
from utils.db_helper import read_customers


customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')


def _payload():
    return request.get_json(silent=True) or {}


def _optional_int(value, field_name):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name}必须是整数')


def _amount(value, field_name, default=0):
    if value is None or value == '':
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name}必须是数字')
    if not isfinite(result):
        raise ValueError(f'{field_name}必须是有效数字')
    return result


def _validate_store(cursor, store_id):
    if store_id is None:
        raise ValueError('请选择所属门店')

    store = cursor.execute(
        'SELECT id, name, status FROM stores WHERE id = ?',
        (store_id,)
    ).fetchone()
    if not store:
        raise ValueError('所属门店不存在')
    if store['status'] != 'active':
        raise ValueError('所属门店已停用，不能关联新客户')
    return store


def _customer_response(cursor, customer_id):
    row = cursor.execute(
        '''
        SELECT
            c.id,
            c.customer_code,
            c.customer_name,
            c.store_id,
            c.contact_person,
            c.phone,
            c.address,
            c.balance,
            c.initial_receivable,
            c.receivable,
            c.bank_name,
            c.bank_account,
            c.bank_code,
            c.tax_number,
            c.remark,
            c.status,
            c.created_at,
            c.updated_at,
            s.name AS store_name,
            s.status AS store_status
        FROM customers c
        LEFT JOIN stores s ON s.id = c.store_id
        WHERE c.id = ?
        ''',
        (customer_id,)
    ).fetchone()
    if not row:
        return None

    customer = dict(row)
    customer['customerCode'] = customer.pop('customer_code', '')
    customer['customerName'] = customer.pop('customer_name', '')
    customer['storeId'] = customer.pop('store_id', None)
    customer['contactPerson'] = customer.pop('contact_person', '')
    customer['initialReceivable'] = customer.pop('initial_receivable', 0)
    customer['bankName'] = customer.pop('bank_name', '')
    customer['bankAccount'] = customer.pop('bank_account', '')
    customer['bankCode'] = customer.pop('bank_code', '')
    customer['taxNumber'] = customer.pop('tax_number', '')
    customer['createdAt'] = customer.pop('created_at', '')
    customer['updatedAt'] = customer.pop('updated_at', '')
    customer['storeName'] = customer.pop('store_name', None)
    customer['storeStatus'] = customer.pop('store_status', None)
    return customer


def _customer_values(data, existing=None):
    existing = existing or {}
    customer_name = str(
        data.get('customerName', existing.get('customerName', '')) or ''
    ).strip()
    customer_code = str(
        data.get('customerCode', existing.get('customerCode', '')) or ''
    ).strip()
    if not customer_name:
        raise ValueError('客户名称不能为空')
    if not customer_code:
        raise ValueError('客户编号不能为空')

    store_id = data.get('storeId', existing.get('storeId'))
    store_id = _optional_int(store_id, '门店ID')

    return {
        'customer_code': customer_code,
        'customer_name': customer_name,
        'store_id': store_id,
        'contact_person': str(
            data.get('contactPerson', existing.get('contactPerson', '')) or ''
        ).strip(),
        'phone': str(data.get('phone', existing.get('phone', '')) or '').strip(),
        'address': str(
            data.get('address', existing.get('address', '')) or ''
        ).strip(),
        'balance': _amount(
            data.get('balance', existing.get('balance', 0)),
            '储值余额'
        ),
        'initial_receivable': _amount(
            data.get(
                'initialDebt',
                existing.get('initialReceivable', existing.get('receivable', 0))
            ),
            '期初欠款'
        ),
        'bank_name': str(
            data.get('bankName', existing.get('bankName', '')) or ''
        ).strip(),
        'bank_account': str(
            data.get('bankAccount', existing.get('bankAccount', '')) or ''
        ).strip(),
        'bank_code': str(
            data.get('bankCode', existing.get('bankCode', '')) or ''
        ).strip(),
        'tax_number': str(
            data.get('taxNumber', existing.get('taxNumber', '')) or ''
        ).strip(),
        'remark': str(data.get('remark', existing.get('remark', '')) or '').strip(),
    }


@customers_bp.route('', methods=['GET'])
@customers_bp.route('/', methods=['GET'])
def get_customers():
    customers = read_customers().get('customers', [])

    customer_name = (request.args.get('customerName') or '').strip().lower()
    phone = (request.args.get('phone') or '').strip()
    store_id = request.args.get('storeId', type=int)
    status = (request.args.get('status') or '').strip()

    if customer_name:
        customers = [
            customer for customer in customers
            if customer_name in customer.get('customerName', '').lower()
        ]
    if phone:
        customers = [
            customer for customer in customers
            if phone in str(customer.get('phone') or '')
        ]
    if store_id is not None:
        customers = [
            customer for customer in customers
            if customer.get('storeId') == store_id
        ]
    if status:
        customers = [
            customer for customer in customers
            if customer.get('status') == status
        ]

    return jsonify(customers)


@customers_bp.route('/receivables', methods=['GET'])
def get_customer_receivables():
    """获取客户应收欠款汇总，供财务应收列表使用。"""
    keyword = (request.args.get('keyword') or '').strip().lower()
    phone = (request.args.get('phone') or '').strip()
    debt_status = (request.args.get('debtStatus') or '').strip()

    with get_db() as conn:
        rows = conn.execute(
            '''
            SELECT
                c.id,
                c.customer_code,
                c.customer_name,
                c.contact_person,
                c.phone,
                c.balance,
                c.initial_receivable,
                c.receivable,
                COALESCE(SUM(
                    CASE
                        WHEN t.transaction_type = 'order_audit'
                         AND t.status = 'active'
                        THEN t.receivable_increase
                        ELSE 0
                    END
                ), 0) AS receivable_increase,
                COALESCE(SUM(
                    CASE
                        WHEN t.status = 'active'
                        THEN t.debt_recovered
                        ELSE 0
                    END
                ), 0) AS debt_recovered,
                COALESCE(SUM(
                    CASE
                        WHEN t.transaction_type = 'order_audit'
                         AND t.status = 'active'
                        THEN t.discount_amount
                        ELSE 0
                    END
                ), 0) AS discount_amount
            FROM customers c
            LEFT JOIN customer_account_transactions t
              ON t.customer_id = c.id
            GROUP BY
                c.id, c.customer_code, c.customer_name,
                c.contact_person, c.phone, c.balance,
                c.initial_receivable, c.receivable
            ORDER BY c.receivable DESC, c.id DESC
            '''
        ).fetchall()

    receivables = []
    for row in rows:
        item = dict(row)
        search_text = ' '.join([
            str(item.get('id') or ''),
            str(item.get('customer_code') or ''),
            str(item.get('customer_name') or ''),
            str(item.get('contact_person') or ''),
        ]).lower()
        if keyword and keyword not in search_text:
            continue
        if phone and phone not in str(item.get('phone') or ''):
            continue

        receivable = float(item.get('receivable') or 0)
        if debt_status == 'outstanding' and receivable <= 0:
            continue
        if debt_status == 'settled' and receivable > 0:
            continue

        balance = float(item.get('balance') or 0)
        receivables.append({
            'customerId': item.get('id'),
            'customerCode': item.get('customer_code') or '',
            'customerName': item.get('customer_name') or '',
            'contactPerson': item.get('contact_person') or '',
            'phone': item.get('phone') or '',
            'storedBalance': round(balance, 2),
            'initialDebt': round(
                float(item.get('initial_receivable') or 0),
                2
            ),
            'receivableIncrease': round(
                float(item.get('receivable_increase') or 0),
                2
            ),
            'debtRecovered': round(
                float(item.get('debt_recovered') or 0),
                2
            ),
            'discountAmount': round(
                float(item.get('discount_amount') or 0),
                2
            ),
            'receivable': round(receivable, 2),
            'netAccountBalance': round(balance - receivable, 2),
        })

    return jsonify({
        'items': receivables,
        'total': len(receivables),
        'summary': {
            'initialDebt': round(
                sum(item['initialDebt'] for item in receivables),
                2
            ),
            'receivableIncrease': round(
                sum(item['receivableIncrease'] for item in receivables),
                2
            ),
            'debtRecovered': round(
                sum(item['debtRecovered'] for item in receivables),
                2
            ),
            'discountAmount': round(
                sum(item['discountAmount'] for item in receivables),
                2
            ),
            'receivable': round(
                sum(item['receivable'] for item in receivables),
                2
            ),
        }
    })


@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    with get_db() as conn:
        customer = _customer_response(conn.cursor(), customer_id)
    if not customer:
        return jsonify({'error': '客户不存在'}), 404
    return jsonify(customer)


@customers_bp.route('', methods=['POST'])
@customers_bp.route('/', methods=['POST'])
def create_customer():
    data = _payload()
    now = datetime.now().isoformat(timespec='seconds')

    try:
        values = _customer_values(data)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        if cursor.execute(
            'SELECT 1 FROM customers WHERE customer_code = ?',
            (values['customer_code'],)
        ).fetchone():
            return jsonify({'error': '客户编号已存在'}), 400

        try:
            _validate_store(cursor, values['store_id'])
        except ValueError as error:
            return jsonify({'error': str(error)}), 400

        cursor.execute(
            '''
            INSERT INTO customers (
                customer_code, customer_name, store_id,
                contact_person, phone, address, balance,
                initial_receivable, receivable,
                bank_name, bank_account, bank_code, tax_number,
                remark, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                values['customer_code'],
                values['customer_name'],
                values['store_id'],
                values['contact_person'],
                values['phone'],
                values['address'],
                values['balance'],
                values['initial_receivable'],
                values['initial_receivable'],
                values['bank_name'],
                values['bank_account'],
                values['bank_code'],
                values['tax_number'],
                values['remark'],
                'active',
                now,
                now,
            )
        )
        customer = _customer_response(cursor, cursor.lastrowid)

    return jsonify(customer), 201


@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = _payload()

    with get_db() as conn:
        cursor = conn.cursor()
        existing = _customer_response(cursor, customer_id)
        if not existing:
            return jsonify({'error': '客户不存在'}), 404

        try:
            values = _customer_values(data, existing)
            _validate_store(cursor, values['store_id'])
        except ValueError as error:
            return jsonify({'error': str(error)}), 400

        if cursor.execute(
            '''
            SELECT 1
            FROM customers
            WHERE customer_code = ? AND id <> ?
            ''',
            (values['customer_code'], customer_id)
        ).fetchone():
            return jsonify({'error': '客户编号已存在'}), 400

        status = data.get('status', existing.get('status') or 'active')
        if status not in ('active', 'inactive'):
            return jsonify({'error': '客户状态无效'}), 400

        receivable = (
            existing.get('receivable', 0)
            + values['initial_receivable']
            - existing.get('initialReceivable', existing.get('receivable', 0))
        )
        if receivable < 0:
            return jsonify({
                'error': '期初欠款调整后不能使当前应收欠款小于0'
            }), 400

        now = datetime.now().isoformat(timespec='seconds')
        cursor.execute(
            '''
            UPDATE customers
            SET customer_code = ?, customer_name = ?, store_id = ?,
                contact_person = ?, phone = ?, address = ?,
                balance = ?, initial_receivable = ?, receivable = ?,
                bank_name = ?, bank_account = ?, bank_code = ?,
                tax_number = ?, remark = ?, status = ?, updated_at = ?
            WHERE id = ?
            ''',
            (
                values['customer_code'],
                values['customer_name'],
                values['store_id'],
                values['contact_person'],
                values['phone'],
                values['address'],
                values['balance'],
                values['initial_receivable'],
                receivable,
                values['bank_name'],
                values['bank_account'],
                values['bank_code'],
                values['tax_number'],
                values['remark'],
                status,
                now,
                customer_id,
            )
        )
        customer = _customer_response(cursor, customer_id)

    return jsonify(customer)


@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    with get_db() as conn:
        cursor = conn.cursor()
        customer = _customer_response(cursor, customer_id)
        if not customer:
            return jsonify({'error': '客户不存在'}), 404

        order_count = cursor.execute(
            'SELECT COUNT(*) AS count FROM orders WHERE customer_id = ?',
            (customer_id,)
        ).fetchone()['count']
        if order_count:
            return jsonify({
                'error': f'客户已关联{order_count}条订单，不能删除'
            }), 409

        cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))

    return jsonify({
        'success': True,
        'message': '删除成功',
        'customer': customer,
    })


@customers_bp.route('/<int:customer_id>/receivable', methods=['GET'])
def get_customer_receivable(customer_id):
    with get_db() as conn:
        row = conn.execute(
            'SELECT receivable FROM customers WHERE id = ?',
            (customer_id,)
        ).fetchone()
        if not row:
            return jsonify({'error': '客户不存在'}), 404

    return jsonify({'receivable': row['receivable'] or 0})
