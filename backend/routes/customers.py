import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite

from flask import Blueprint, jsonify, request

from utils.db import get_db
from utils.db_helper import read_customers


customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')

_MONEY_QUANT = Decimal('0.01')
_DEBT_TRANSACTION_TYPES = (
    'order_audit',
    'customer_return',
    'customer_payment',
)


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


def _debt_money(value):
    """将账务金额统一转换为两位小数，避免商品分摊出现浮点尾差。"""
    if value in (None, ''):
        value = 0
    try:
        return Decimal(str(value)).quantize(
            _MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0.00')


def _debt_float(value):
    return float(_debt_money(value))


def _debt_json_list(value):
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _debt_product(item):
    """统一订单商品 JSON 与退货商品表的字段。"""
    item = dict(item or {})
    quantity = item.get('quantity', 0)
    price = item.get('price', 0)
    subtotal = item.get('amount')
    if subtotal in (None, ''):
        subtotal = item.get('total_amount')
    if subtotal in (None, ''):
        subtotal = _debt_money(quantity) * _debt_money(price)

    return {
        'productId': item.get('product_id', item.get('productId')),
        'productCode': item.get('product_code', item.get('productCode', '')) or '',
        'name': (
            item.get('goods_name')
            or item.get('goodsName')
            or item.get('name')
            or item.get('productName')
            or ''
        ),
        'specification': (
            item.get('specification')
            or item.get('spec')
            or item.get('specificationName')
            or ''
        ),
        'quantity': _debt_float(quantity),
        'unit': item.get('unit') or '',
        'price': _debt_float(price),
        'subtotal': _debt_float(subtotal),
        'warehouseId': item.get('warehouse_id', item.get('warehouseId')),
        'remark': item.get('remark') or '',
    }


def _allocate_debt(products, debt_amount, cumulative_before):
    """按商品小计分摊一条流水，并把累计欠款精确到分。"""
    if not products:
        return []

    debt_amount = _debt_money(debt_amount)
    total_subtotal = sum(
        (_debt_money(product.get('subtotal')) for product in products),
        Decimal('0.00'),
    )
    product_count = len(products)
    allocated = []
    allocated_before = Decimal('0.00')

    for index, product in enumerate(products):
        if index == product_count - 1:
            amount = debt_amount - allocated_before
        elif total_subtotal == 0:
            amount = (debt_amount / product_count).quantize(
                _MONEY_QUANT,
                rounding=ROUND_HALF_UP,
            )
        else:
            amount = (
                debt_amount
                * _debt_money(product.get('subtotal'))
                / total_subtotal
            ).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)

        allocated_before += amount
        cumulative_before += amount
        product['allocatedDebt'] = _debt_float(amount)
        product['cumulativeDebt'] = _debt_float(cumulative_before)
        allocated.append(product)

    return allocated


def _order_row_for_transaction(cursor, transaction):
    order = None
    if transaction['order_id']:
        order = cursor.execute(
            'SELECT * FROM orders WHERE id = ?',
            (transaction['order_id'],),
        ).fetchone()
    if not order and transaction['order_number']:
        order = cursor.execute(
            '''
            SELECT * FROM orders
            WHERE order_number = ?
            ORDER BY id DESC
            LIMIT 1
            ''',
            (transaction['order_number'],),
        ).fetchone()
    return order


def _return_row_for_transaction(cursor, transaction):
    return cursor.execute(
        '''
        SELECT *
        FROM return_orders
        WHERE account_transaction_id = ?
           OR return_number = ?
        ORDER BY id DESC
        LIMIT 1
        ''',
        (transaction['id'], transaction['order_number'] or ''),
    ).fetchone()


def _payment_row_for_transaction(cursor, transaction):
    payment = None
    if transaction['payment_id']:
        payment = cursor.execute(
            'SELECT * FROM payment_receipts WHERE id = ?',
            (transaction['payment_id'],),
        ).fetchone()
    if not payment and transaction['payment_number']:
        payment = cursor.execute(
            '''
            SELECT *
            FROM payment_receipts
            WHERE document_no = ?
            ORDER BY id DESC
            LIMIT 1
            ''',
            (transaction['payment_number'],),
        ).fetchone()
    return payment


def _debt_record_from_transaction(cursor, transaction):
    tx_type = transaction['transaction_type']
    record_id = transaction['id']
    products = []
    record = {
        'id': f'tx-{record_id}',
        'transactionId': record_id,
        'businessDate': transaction['created_at'] or '',
        'docNumber': (
            transaction['order_number']
            or transaction['payment_number']
            or f'TX{record_id}'
        ),
        'businessType': '',
        'orderAmount': 0.0,
        'paidAmount': 0.0,
        'storedBalanceApplied': _debt_float(
            transaction['stored_balance_applied']
        ),
        '_receivableIncrease': _debt_float(
            transaction['receivable_increase']
        ),
        'debtAmount': _debt_float(transaction['receivable_change']),
        'currentDebt': _debt_float(transaction['receivable_after']),
        'products': products,
        'hasMultipleProducts': False,
        'productCount': 0,
        'remark': '',
    }

    if tx_type == 'order_audit':
        order = _order_row_for_transaction(cursor, transaction)
        if order and order['audit_state'] != 1:
            return None
        if order:
            record.update({
                'businessDate': order['date'] or record['businessDate'],
                'docNumber': order['order_number'] or record['docNumber'],
                'orderAmount': _debt_float(order['should_receive']),
                'paidAmount': _debt_float(
                    _debt_money(order['current_payment'])
                    + _debt_money(transaction['stored_balance_applied'])
                ),
                'remark': order['remark'] or '',
            })
            products = [
                _debt_product(item)
                for item in _debt_json_list(order['order_goods'])
                if isinstance(item, dict)
            ]
        record['businessType'] = 'ORDER'
    elif tx_type == 'customer_return':
        return_row = _return_row_for_transaction(cursor, transaction)
        if return_row and return_row['status'] not in ('audited', 'completed'):
            return None
        if return_row:
            record.update({
                'businessDate': return_row['return_date'] or record['businessDate'],
                'docNumber': return_row['return_number'] or record['docNumber'],
                'orderAmount': _debt_float(return_row['total_amount']),
                'paidAmount': _debt_float(return_row['refund_amount']),
                'remark': return_row['remark'] or '',
            })
            item_rows = cursor.execute(
                '''
                SELECT *
                FROM return_order_items
                WHERE return_id = ?
                ORDER BY line_no, id
                ''',
                (return_row['id'],),
            ).fetchall()
            products = [_debt_product(item) for item in item_rows]
        record['businessType'] = 'RETURN'
    elif tx_type == 'customer_payment':
        payment = _payment_row_for_transaction(cursor, transaction)
        if payment and payment['status'] != 'audited':
            return None
        if payment:
            record.update({
                'businessDate': payment['document_date'] or record['businessDate'],
                'docNumber': payment['document_no'] or record['docNumber'],
                'paidAmount': _debt_float(payment['payment_amount']),
                'remark': payment['remark'] or '',
            })
        record['businessType'] = 'PAYMENT'
    else:
        return None

    record['products'] = products
    record['productCount'] = len(products)
    record['hasMultipleProducts'] = len(products) > 1
    return record


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
            c.balance_at,
            c.initial_receivable,
            c.initial_receivable_at,
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
    customer['balanceAt'] = customer.pop('balance_at', None)
    customer['initialReceivable'] = customer.pop('initial_receivable', 0)
    customer['initialReceivableAt'] = customer.pop(
        'initial_receivable_at',
        None,
    )
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

    balance = _amount(
        data.get('balance', existing.get('balance', 0)),
        '储值余额'
    )
    initial_receivable = _amount(
        data.get(
            'initialDebt',
            existing.get('initialReceivable', 0)
        ),
        '期初欠款'
    )
    if balance < 0:
        raise ValueError('储值余额不能小于0')
    if initial_receivable < 0:
        raise ValueError('期初欠款不能小于0')

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
        'balance': balance,
        'initial_receivable': initial_receivable,
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
    store_id = request.args.get('storeId', type=int)

    with get_db() as conn:
        rows = conn.execute(
            '''
            SELECT
                c.id,
                c.customer_code,
                c.customer_name,
                c.contact_person,
                c.phone,
                c.store_id,
                s.name AS store_name,
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
                        WHEN t.transaction_type IN (
                            'order_audit',
                            'customer_payment'
                        )
                         AND t.status = 'active'
                        THEN t.discount_amount
                        ELSE 0
                    END
                ), 0) AS discount_amount
            FROM customers c
            LEFT JOIN stores s
              ON s.id = c.store_id
            LEFT JOIN customer_account_transactions t
              ON t.customer_id = c.id
            WHERE (? IS NULL OR c.store_id = ?)
            GROUP BY
                c.id, c.customer_code, c.customer_name,
                c.contact_person, c.phone, c.store_id, s.name, c.balance,
                c.initial_receivable, c.receivable
            ORDER BY c.receivable DESC, c.id DESC
            ''',
            (store_id, store_id)
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
            'storeId': item.get('store_id'),
            'storeName': item.get('store_name') or '',
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


@customers_bp.route('/<int:customer_id>/debt-details', methods=['GET'])
def get_customer_debt_details(customer_id):
    """获取客户对账单及期初欠款、储值虚拟记录。"""
    requested_type = (request.args.get('businessType') or '').strip().upper()
    allowed_types = {'', 'ORDER', 'RETURN', 'PAYMENT', 'INITIAL', 'BALANCE'}
    if requested_type not in allowed_types:
        return jsonify({
            'error': '业务类型仅支持ORDER、RETURN、PAYMENT、INITIAL、BALANCE'
        }), 400

    start_date = (request.args.get('startDate') or '').strip()
    end_date = (request.args.get('endDate') or '').strip()
    expand_products = (
        str(request.args.get('expandProducts', 'false')).lower()
        in ('1', 'true', 'yes')
    )

    with get_db() as conn:
        cursor = conn.cursor()
        customer = cursor.execute(
            '''
            SELECT c.id, c.customer_code, c.customer_name, c.store_id,
                   c.balance, c.balance_at,
                   c.initial_receivable, c.initial_receivable_at,
                   c.receivable, c.created_at, s.name AS store_name
            FROM customers c
            LEFT JOIN stores s ON s.id = c.store_id
            WHERE c.id = ?
            ''',
            (customer_id,),
        ).fetchone()
        if not customer:
            return jsonify({'error': '客户不存在'}), 404

        transactions = cursor.execute(
            '''
            SELECT *
            FROM customer_account_transactions
            WHERE customer_id = ?
              AND status = 'active'
              AND transaction_type IN (?, ?, ?)
            ORDER BY created_at ASC, id ASC
            ''',
            (customer_id, *_DEBT_TRANSACTION_TYPES),
        ).fetchall()

        records = []
        for transaction in transactions:
            record = _debt_record_from_transaction(cursor, transaction)
            if not record:
                continue
            records.append(record)

        initial_debt = _debt_money(customer['initial_receivable'])
        if initial_debt > 0:
            records.append({
                'id': f'initial-{customer_id}',
                'transactionId': 0,
                'businessDate': (
                    customer['initial_receivable_at']
                    or customer['created_at']
                    or ''
                ),
                'docNumber': '期初欠款',
                'businessType': 'INITIAL',
                'orderAmount': _debt_float(initial_debt),
                'paidAmount': 0.0,
                'storedBalanceApplied': 0.0,
                # 期初欠款已经单独计入 summary.initialDebt；这里仅作为
                # 对账起点参与 currentDebt，避免在新增应收里重复计算。
                '_receivableIncrease': 0.0,
                'debtAmount': _debt_float(initial_debt),
                'currentDebt': 0.0,
                'products': [],
                'hasMultipleProducts': False,
                'productCount': 0,
                'remark': '客户期初欠款',
            })

        stored_balance = _debt_money(customer['balance'])
        if stored_balance > 0:
            records.append({
                'id': f'balance-{customer_id}',
                'transactionId': 0,
                'businessDate': (
                    customer['balance_at']
                    or customer['created_at']
                    or ''
                ),
                'docNumber': '储值调整',
                'businessType': 'BALANCE',
                'orderAmount': 0.0,
                'paidAmount': 0.0,
                'balanceAmount': _debt_float(stored_balance),
                'storedBalanceApplied': 0.0,
                '_receivableIncrease': 0.0,
                'debtAmount': 0.0,
                'currentDebt': 0.0,
                'products': [],
                'hasMultipleProducts': False,
                'productCount': 0,
                'remark': '客户储值余额',
            })

    # 账务累计必须基于全部有效流水计算，不能因筛选日期/类型而改变历史累计欠款。
    records.sort(
        key=lambda item: (
            str(item['businessDate'] or '').replace('T', ' '),
            item.get('transactionId') or 0,
            item['id'],
        )
    )
    cumulative = Decimal('0.00')
    for record in records:
        debt_amount = _debt_money(record['debtAmount'])
        record['debtAmount'] = _debt_float(debt_amount)
        if expand_products and record['products']:
            record['products'] = _allocate_debt(
                record['products'],
                debt_amount,
                cumulative,
            )
            cumulative = (
                _debt_money(record['products'][-1]['cumulativeDebt'])
                if record['products']
                else cumulative + debt_amount
            )
        else:
            cumulative += debt_amount
        record['currentDebt'] = _debt_float(cumulative)
        if not expand_products:
            record['products'] = []
            record['productCount'] = 0
            record['hasMultipleProducts'] = False

    # 日期筛选只影响列表，不影响每条记录已计算好的累计欠款。
    filtered_records = [
        record for record in records
        if (not requested_type or record['businessType'] == requested_type)
        and (not start_date or str(record['businessDate'])[:10] >= start_date)
        and (not end_date or str(record['businessDate'])[:10] <= end_date)
    ]

    initial_debt = _debt_money(customer['initial_receivable'])
    stored_balance = _debt_money(customer['balance'])
    receivable_increase = sum(
        (_debt_money(record.get('_receivableIncrease'))
         for record in records
         if _debt_money(record.get('_receivableIncrease')) > 0),
        Decimal('0.00'),
    )
    debt_recovered = max(
        Decimal('0.00'),
        initial_debt + receivable_increase
        - _debt_money(customer['receivable']),
    )

    response_records = []
    for record in filtered_records:
        response_record = dict(record)
        response_record.pop('_receivableIncrease', None)
        if not expand_products:
            response_record.pop('products', None)
        response_records.append(response_record)

    return jsonify({
        'customerId': customer['id'],
        'customerCode': customer['customer_code'] or '',
        'customerName': customer['customer_name'] or '',
        'storeId': customer['store_id'],
        'storeName': customer['store_name'] or '',
        'initialDebt': _debt_float(initial_debt),
        'initialDebtAt': customer['initial_receivable_at'],
        'storedBalance': _debt_float(stored_balance),
        'balanceAt': customer['balance_at'],
        'totalReceivable': _debt_float(customer['receivable']),
        'summary': {
            'initialDebt': _debt_float(initial_debt),
            'storedBalance': _debt_float(stored_balance),
            'receivableIncrease': _debt_float(receivable_increase),
            'debtRecovered': _debt_float(debt_recovered),
            # 对账单不单独展示优惠调整，优惠金额仍留在原收款/订单流水中。
            'discountAmount': 0.0,
            'receivable': _debt_float(customer['receivable']),
        },
        'records': response_records,
        'total': len(response_records),
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

        # 将数值转为float以避免SQLite绑定错误
        balance_float = float(values['balance'])
        initial_receivable_float = float(values['initial_receivable'])

        cursor.execute(
            '''
            INSERT INTO customers (
                customer_code, customer_name, store_id,
                contact_person, phone, address, balance,
                balance_at, initial_receivable, initial_receivable_at,
                receivable,
                bank_name, bank_account, bank_code, tax_number,
                remark, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                values['customer_code'],
                values['customer_name'],
                values['store_id'],
                values['contact_person'],
                values['phone'],
                values['address'],
                balance_float,
                now if balance_float > 0 else None,
                initial_receivable_float,
                now if initial_receivable_float > 0 else None,
                initial_receivable_float,
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

        old_initial = _debt_money(existing.get('initialReceivable', 0))
        new_initial = _debt_money(values['initial_receivable'])
        old_balance = _debt_money(existing.get('balance', 0))
        new_balance = _debt_money(values['balance'])
        receivable = (
            _debt_money(existing.get('receivable', 0))
            + new_initial
            - old_initial
        )
        if receivable < 0:
            return jsonify({
                'error': '期初欠款调整后不能使当前应收欠款小于0'
            }), 400

        now = datetime.now().isoformat(timespec='seconds')
        initial_receivable_at = existing.get('initialReceivableAt')
        if new_initial != old_initial:
            initial_receivable_at = now if new_initial > 0 else None
        elif new_initial > 0 and not initial_receivable_at:
            initial_receivable_at = existing.get('createdAt') or now

        balance_at = existing.get('balanceAt')
        if new_balance != old_balance:
            balance_at = now if new_balance > 0 else None
        elif new_balance > 0 and not balance_at:
            balance_at = existing.get('createdAt') or now

        # 将Decimal转为float以避免SQLite绑定错误
        balance_float = float(values['balance'])
        initial_receivable_float = float(values['initial_receivable'])
        receivable_float = float(receivable)

        cursor.execute(
            '''
            UPDATE customers
            SET customer_code = ?, customer_name = ?, store_id = ?,
                contact_person = ?, phone = ?, address = ?,
                balance = ?, balance_at = ?,
                initial_receivable = ?, initial_receivable_at = ?,
                receivable = ?,
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
                balance_float,
                balance_at,
                initial_receivable_float,
                initial_receivable_at,
                receivable_float,
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
