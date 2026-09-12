"""销售/原材料退货单及客户应收核销 API。"""

import json
import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, jsonify, request

from utils.db import get_db


returns_bp = Blueprint('returns', __name__, url_prefix='/api/returns')
_write_lock = threading.Lock()
_MONEY_QUANT = Decimal('0.01')


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _number(value, field='数值', default=Decimal('0.00')):
    if value in (None, ''):
        return default
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f'{field}必须是有效数字')
    if not result.is_finite():
        raise ValueError(f'{field}必须是有限数字')
    return result


def _money(value, field='金额'):
    return _number(value, field).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)


def _date(value):
    text = str(value or '').strip()
    try:
        datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        raise ValueError('日期格式必须为YYYY-MM-DD')
    return text


def _int(value, field, required=False):
    if value in (None, ''):
        if required:
            raise ValueError(f'请选择{field}')
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field}必须是整数')


def _text(value, max_length=None):
    text = '' if value is None else str(value).strip()
    return text[:max_length] if max_length else text


def _operator():
    return _text(request.headers.get('Username') or '系统用户', 80) or '系统用户'


def _next_return_number(conn, return_date):
    prefix = f'TH{return_date.replace("-", "")}'
    rows = conn.execute(
        'SELECT return_number FROM return_orders WHERE return_number LIKE ?',
        (f'{prefix}%',),
    ).fetchall()
    sequence = 0
    for row in rows:
        suffix = str(row['return_number'] or '')[len(prefix):]
        if suffix.isdigit():
            sequence = max(sequence, int(suffix))
    return f'{prefix}{sequence + 1:04d}'


def _serialize_item(row):
    item = dict(row)
    return {
        'id': item.get('id'),
        'lineNo': item.get('line_no'),
        'productType': item.get('product_type') or 'finished-product',
        'productId': item.get('product_id'),
        'productCode': item.get('product_code') or '',
        'goodsName': item.get('goods_name') or '',
        'specification': item.get('specification') or '',
        'unit': item.get('unit') or '',
        'warehouseId': item.get('warehouse_id'),
        'packages': round(float(item.get('packages') or 0), 4),
        'quantity': round(float(item.get('quantity') or 0), 4),
        'price': round(float(item.get('price') or 0), 2),
        'amount': round(float(item.get('amount') or 0), 2),
        'taxRate': round(float(item.get('tax_rate') or 0), 2),
        'taxIncludedPrice': round(float(item.get('tax_included_price') or 0), 2),
        'taxAmount': round(float(item.get('tax_amount') or 0), 2),
        'taxIncludedAmount': round(float(item.get('tax_included_amount') or 0), 2),
        'remark': item.get('remark') or '',
    }


def _serialize_return(conn, return_id, include_items=True):
    row = conn.execute(
        '''
        SELECT r.*, c.customer_code, c.customer_name, c.contact_person,
               c.phone, s.name AS store_name
        FROM return_orders r
        JOIN customers c ON c.id = r.customer_id
        LEFT JOIN stores s ON s.id = r.store_id
        WHERE r.id = ?
        ''',
        (return_id,),
    ).fetchone()
    if not row:
        return None
    item = dict(row)
    result = {
        'id': item['id'],
        'returnNumber': item['return_number'],
        'originalOrderNumber': item['original_order_number'] or '',
        'returnDate': item['return_date'],
        'storeId': item['store_id'],
        'storeName': item.get('store_name') or '',
        'customerId': item['customer_id'],
        'customerCode': item.get('customer_code') or '',
        'customerName': item.get('customer_name') or '',
        'contactPerson': item.get('contact_person') or '',
        'phone': item.get('phone') or '',
        'productType': item.get('product_type') or 'finished-product',
        'taxEnabled': bool(item.get('tax_enabled')),
        'totalQuantity': round(float(item.get('total_quantity') or 0), 4),
        'totalPackages': round(float(item.get('total_packages') or 0), 4),
        'totalAmount': round(float(item.get('total_amount') or 0), 2),
        'totalTaxAmount': round(float(item.get('total_tax_amount') or 0), 2),
        'totalTaxIncludedAmount': round(float(item.get('total_tax_included_amount') or 0), 2),
        'refundAmount': round(float(item.get('refund_amount') or 0), 2),
        'writeoffAmount': round(float(item.get('writeoff_amount') or 0), 2),
        'debtBefore': round(float(item.get('debt_before') or 0), 2),
        'debtAfter': round(float(item.get('debt_after') or 0), 2),
        'settlementAccount': item.get('settlement_account') or '',
        'salesPerson': item.get('sales_person') or '',
        'creator': item.get('creator') or '',
        'packaging': item.get('packaging') or '',
        'remark': item.get('remark') or '',
        'status': item.get('status') or 'completed',
        'accountTransactionId': item.get('account_transaction_id'),
        'createdAt': item.get('created_at') or '',
        'updatedAt': item.get('updated_at') or '',
    }
    if include_items:
        rows = conn.execute(
            'SELECT * FROM return_order_items WHERE return_id = ? ORDER BY line_no, id',
            (return_id,),
        ).fetchall()
        result['items'] = [_serialize_item(row) for row in rows]
    return result


def _normalize_items(conn, data, product_type):
    raw_items = data.get('items') or []
    if not isinstance(raw_items, list):
        raise ValueError('商品明细必须是数组')

    table = 'raw_material_products' if product_type == 'raw-material' else 'products'
    normalized = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        product_id = _int(raw.get('productId', raw.get('product_id')), '商品')
        name = _text(raw.get('goodsName', raw.get('name', raw.get('productName'))), 160)
        if product_id is None and not name:
            continue
        if product_id is not None:
            exists = conn.execute(
                f'SELECT 1 FROM {table} WHERE id = ?', (product_id,)
            ).fetchone()
            if not exists:
                raise ValueError(f'商品ID {product_id} 不存在')
        quantity = _number(raw.get('quantity'), '数量')
        packages = _number(raw.get('packages'), '件数')
        price = _money(raw.get('price'), '单价')
        amount = _money(raw.get('amount'), '总金额')
        tax_rate = _number(raw.get('taxRate', raw.get('tax_rate')), '税率')
        if quantity < 0 or packages < 0 or price < 0 or amount < 0:
            raise ValueError('数量、件数、单价和金额不能小于0')
        if tax_rate < 0 or tax_rate > 100:
            raise ValueError('税率必须在0到100之间')
        tax_included_price = _money(
            raw.get('taxIncludedPrice', raw.get('tax_included_price')),
            '含税单价',
        )
        tax_amount = (amount * tax_rate / Decimal('100')).quantize(
            _MONEY_QUANT, rounding=ROUND_HALF_UP
        )
        tax_included_amount = (amount + tax_amount).quantize(
            _MONEY_QUANT, rounding=ROUND_HALF_UP
        )
        normalized.append({
            'product_type': product_type,
            'product_id': product_id,
            'product_code': _text(raw.get('productCode', raw.get('code')), 80),
            'goods_name': name,
            'specification': _text(raw.get('specification', raw.get('spec')), 160),
            'unit': _text(raw.get('unit'), 40),
            'warehouse_id': _int(raw.get('warehouseId', raw.get('warehouse_id')), '仓库'),
            'packages': packages,
            'quantity': quantity,
            'price': price,
            'amount': amount,
            'tax_rate': tax_rate,
            'tax_included_price': tax_included_price,
            'tax_amount': tax_amount,
            'tax_included_amount': tax_included_amount,
            'remark': _text(raw.get('remark'), 500),
        })
    if not normalized:
        raise ValueError('请至少添加一条商品明细')
    return normalized


@returns_bp.route('', methods=['GET'])
def list_returns():
    store_id = request.args.get('storeId', type=int)
    customer_id = request.args.get('customerId', type=int)
    status = _text(request.args.get('status'), 30)
    with get_db() as conn:
        sql = '''
            SELECT r.*, c.customer_code, c.customer_name, c.contact_person,
                   c.phone, s.name AS store_name,
                   GROUP_CONCAT(i.goods_name, '、') AS goods_name
            FROM return_orders r
            JOIN customers c ON c.id = r.customer_id
            LEFT JOIN stores s ON s.id = r.store_id
            LEFT JOIN return_order_items i ON i.return_id = r.id
            WHERE 1 = 1
        '''
        params = []
        if store_id is not None:
            sql += ' AND r.store_id = ?'
            params.append(store_id)
        if customer_id is not None:
            sql += ' AND r.customer_id = ?'
            params.append(customer_id)
        if status:
            sql += ' AND r.status = ?'
            params.append(status)
        sql += ' GROUP BY r.id ORDER BY r.return_date DESC, r.id DESC'
        rows = conn.execute(sql, params).fetchall()
        items = []
        for row in rows:
            item = _serialize_return(conn, row['id'], include_items=False)
            item['goodsName'] = row['goods_name'] or ''
            items.append(item)
        return jsonify(items)


@returns_bp.route('/<int:return_id>', methods=['GET'])
def get_return(return_id):
    with get_db() as conn:
        item = _serialize_return(conn, return_id)
        if not item:
            return jsonify({'success': False, 'message': '退货单不存在'}), 404
        return jsonify(item)


@returns_bp.route('', methods=['POST'])
def create_return():
    data = request.get_json(silent=True) or {}
    try:
        product_type = _text(data.get('productType'), 30) or 'finished-product'
        if product_type not in ('finished-product', 'raw-material'):
            raise ValueError('商品类型无效')
        store_id = _int(data.get('storeId'), '门店', required=True)
        customer_id = _int(data.get('customerId'), '客户', required=True)
        return_date = _date(data.get('returnDate'))
        original_order_number = _text(data.get('originalOrderNumber'), 80)
        if not original_order_number:
            raise ValueError('原订单号不能为空')
        refund_amount = _money(data.get('refundAmount'), '本次退款')
        if refund_amount < 0:
            raise ValueError('本次退款不能小于0')

        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                store = conn.execute(
                    'SELECT id, name, status FROM stores WHERE id = ?', (store_id,)
                ).fetchone()
                if not store or store['status'] != 'active':
                    raise ValueError('门店不存在或已停用')
                customer = conn.execute(
                    '''
                    SELECT id, customer_name, store_id, receivable, status, balance
                    FROM customers WHERE id = ?
                    ''',
                    (customer_id,),
                ).fetchone()
                if not customer or customer['status'] != 'active':
                    raise ValueError('客户不存在或已停用')
                if customer['store_id'] != store_id:
                    raise ValueError('客户与门店不匹配')

                items = _normalize_items(conn, data, product_type)
                return_amount = _money(
                    data.get('returnAmount', data.get('totalAmount')),
                    '实退金额',
                )
                if return_amount <= 0:
                    return_amount = sum(
                        (item['amount'] for item in items), Decimal('0.00')
                    ).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
                if return_amount <= 0:
                    raise ValueError('实退金额必须大于0')
                debt_before = max(
                    _money(customer['receivable'], '客户欠款'),
                    Decimal('0.00'),
                )
                if return_amount > debt_before:
                    raise ValueError(
                        f'实退金额不能超过客户当前欠款（{debt_before:.2f}元）'
                    )
                if refund_amount > return_amount:
                    raise ValueError('本次退款不能超过实退金额')

                debt_after = (debt_before - return_amount).quantize(
                    _MONEY_QUANT, rounding=ROUND_HALF_UP
                )
                writeoff_amount = return_amount - refund_amount
                now = _now()
                return_number = _text(data.get('returnNumber'), 60)
                if not return_number:
                    return_number = _next_return_number(conn, return_date)
                duplicate = conn.execute(
                    'SELECT 1 FROM return_orders WHERE return_number = ?',
                    (return_number,),
                ).fetchone()
                if duplicate:
                    raise ValueError('退货单号已存在')

                total_quantity = sum((i['quantity'] for i in items), Decimal('0'))
                total_packages = sum((i['packages'] for i in items), Decimal('0'))
                total_amount = sum((i['amount'] for i in items), Decimal('0'))
                total_tax_amount = sum((i['tax_amount'] for i in items), Decimal('0'))
                total_tax_included = sum(
                    (i['tax_included_amount'] for i in items), Decimal('0')
                )
                cursor = conn.execute(
                    '''
                    INSERT INTO return_orders (
                        return_number, original_order_number, return_date,
                        store_id, customer_id, product_type, tax_enabled,
                        total_quantity, total_packages, total_amount,
                        total_tax_amount, total_tax_included_amount, refund_amount,
                        writeoff_amount, debt_before, debt_after,
                        settlement_account, sales_person, creator, packaging,
                        remark, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, 'completed', ?, ?)
                    ''',
                    (
                        return_number, original_order_number, return_date,
                        store_id, customer_id, product_type,
                        int(bool(data.get('taxEnabled'))),
                        float(total_quantity), float(total_packages),
                        float(return_amount), float(total_tax_amount),
                        float(total_tax_included), float(refund_amount),
                        float(writeoff_amount), float(debt_before),
                        float(debt_after),
                        _text(data.get('settlementAccount') or f"{store['name']}结算账户", 120),
                        _text(data.get('salesPerson'), 80),
                        _text(data.get('creator'), 80),
                        _text(data.get('packaging'), 80),
                        _text(data.get('remark'), 1000),
                        now, now,
                    ),
                )
                return_id = cursor.lastrowid
                for line_no, item in enumerate(items, start=1):
                    conn.execute(
                        '''
                        INSERT INTO return_order_items (
                            return_id, line_no, product_type, product_id,
                            product_code, goods_name, specification, unit,
                            warehouse_id, packages, quantity, price, amount,
                            tax_rate, tax_included_price, tax_amount,
                            tax_included_amount, remark
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            return_id, line_no, item['product_type'],
                            item['product_id'], item['product_code'],
                            item['goods_name'], item['specification'], item['unit'],
                            item['warehouse_id'], float(item['packages']),
                            float(item['quantity']), float(item['price']),
                            float(item['amount']), float(item['tax_rate']),
                            float(item['tax_included_price']),
                            float(item['tax_amount']),
                            float(item['tax_included_amount']), item['remark'],
                        ),
                    )

                conn.execute(
                    '''
                    UPDATE customers
                    SET receivable = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (float(debt_after), now, customer_id),
                )
                transaction_cursor = conn.execute(
                    '''
                    INSERT INTO customer_account_transactions (
                        customer_id, order_number, transaction_type,
                        order_receivable, discount_amount, balance_change,
                        receivable_change, balance_after, receivable_after,
                        status, operator, created_at
                    ) VALUES (?, ?, 'customer_return', ?, ?, 0, ?, ?, ?,
                              'active', ?, ?)
                    ''',
                    (
                        customer_id, return_number, float(return_amount),
                        float(writeoff_amount), float(-return_amount),
                        float(customer['balance'] or 0), float(debt_after),
                        _operator(), now,
                    ),
                )
                conn.execute(
                    '''
                    UPDATE return_orders
                    SET account_transaction_id = ?
                    WHERE id = ?
                    ''',
                    (transaction_cursor.lastrowid, return_id),
                )
                result = _serialize_return(conn, return_id)

        return jsonify({
            'success': True,
            'message': (
                f'退货单保存成功，客户应收已核销{return_amount:.2f}元；'
                f'实际退款{refund_amount:.2f}元'
            ),
            'returnNumber': result['returnNumber'],
            'returnId': result['id'],
            'returnOrder': result,
        }), 201
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': f'保存退货单失败：{exc}'}), 500


@returns_bp.route('/<int:return_id>', methods=['DELETE'])
def delete_return(return_id):
    """删除退货单并反向恢复客户应收，仅允许撤销最近的账户流水。"""
    now = _now()
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                item = conn.execute(
                    'SELECT * FROM return_orders WHERE id = ?', (return_id,)
                ).fetchone()
                if not item:
                    return jsonify({'success': False, 'message': '退货单不存在'}), 404
                transaction = conn.execute(
                    '''
                    SELECT * FROM customer_account_transactions
                    WHERE id = ? AND transaction_type = 'customer_return'
                      AND status = 'active'
                    ''',
                    (item['account_transaction_id'],),
                ).fetchone()
                customer = conn.execute(
                    'SELECT * FROM customers WHERE id = ?', (item['customer_id'],)
                ).fetchone()
                if not transaction or not customer:
                    return jsonify({'success': False, 'message': '退货单账户流水不存在'}), 409
                current_debt = _money(customer['receivable'])
                return_amount = _money(item['total_amount'])
                if current_debt + return_amount < 0:
                    return jsonify({'success': False, 'message': '客户应收状态异常，无法撤销'}), 409
                debt_after = current_debt + return_amount
                conn.execute(
                    'UPDATE customers SET receivable = ?, updated_at = ? WHERE id = ?',
                    (float(debt_after), now, customer['id']),
                )
                conn.execute(
                    '''
                    UPDATE customer_account_transactions
                    SET status = 'reversed', reversed_at = ?
                    WHERE id = ?
                    ''',
                    (now, transaction['id']),
                )
                conn.execute('DELETE FROM return_orders WHERE id = ?', (return_id,))
        return jsonify({'success': True, 'message': '退货单已删除，客户应收已恢复'})
    except Exception as exc:
        return jsonify({'success': False, 'message': f'删除退货单失败：{exc}'}), 500
