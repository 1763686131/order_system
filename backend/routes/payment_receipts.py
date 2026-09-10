"""收款单、审核入账与反审核 API。"""
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os
import threading
import uuid

from flask import Blueprint, jsonify, request

from utils.db import get_db


payment_receipts_bp = Blueprint(
    'payment_receipts',
    __name__,
    url_prefix='/api/payment-receipts'
)

MONEY_QUANT = Decimal('0.01')
_write_lock = threading.Lock()
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

if os.path.exists('/app/frontend/index.html') and os.path.isdir('/app/uploads'):
    BASE_UPLOAD_DIR = '/app/uploads'
else:
    BASE_UPLOAD_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'uploads'
    )


def _money(value, field_name='金额'):
    try:
        result = Decimal(str(value if value not in (None, '') else 0))
        if not result.is_finite():
            raise InvalidOperation
        return result.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f'{field_name}必须是有效数字')


def _date(value):
    date_text = str(value or '').strip()
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError('单据日期格式必须为YYYY-MM-DD')
    return date_text


def _operator(default='王醒'):
    return str(request.headers.get('Username') or default).strip() or default


def _next_document_no(conn, document_date):
    prefix = f"SK{document_date.replace('-', '')}"
    rows = conn.execute(
        '''
        SELECT document_no
        FROM payment_receipts
        WHERE document_no LIKE ?
        ''',
        (f'{prefix}%',)
    ).fetchall()
    sequence = 0
    for row in rows:
        suffix = str(row['document_no'] or '')[len(prefix):]
        if suffix.isdigit():
            sequence = max(sequence, int(suffix))
    return f'{prefix}{sequence + 1:03d}'


def _receipt_row(conn, receipt_id):
    return conn.execute(
        '''
        SELECT
            p.*,
            c.customer_code,
            c.customer_name,
            c.contact_person,
            c.phone,
            s.name AS store_name
        FROM payment_receipts p
        JOIN customers c ON c.id = p.customer_id
        LEFT JOIN stores s ON s.id = p.store_id
        WHERE p.id = ?
        ''',
        (receipt_id,)
    ).fetchone()


def _serialize(row):
    if not row:
        return None
    item = dict(row)
    return {
        'id': item['id'],
        'documentNo': item.get('document_no') or '',
        'documentDate': item.get('document_date') or '',
        'storeId': item.get('store_id'),
        'storeName': item.get('store_name') or '',
        'customerId': item.get('customer_id'),
        'customerCode': item.get('customer_code') or '',
        'customerName': item.get('customer_name') or '',
        'contactPerson': item.get('contact_person') or '',
        'phone': item.get('phone') or '',
        'settlementAccount': item.get('settlement_account') or '',
        'paymentMethod': item.get('payment_method') or '',
        'paymentAmount': round(float(item.get('payment_amount') or 0), 2),
        'discountAmount': round(float(item.get('discount_amount') or 0), 2),
        'totalAmount': round(float(item.get('total_amount') or 0), 2),
        'writeoffAmount': round(float(item.get('writeoff_amount') or 0), 2),
        'advanceAmount': round(float(item.get('advance_amount') or 0), 2),
        'debtBefore': round(float(item.get('debt_before') or 0), 2),
        'debtAfter': round(float(item.get('debt_after') or 0), 2),
        'balanceBefore': round(float(item.get('balance_before') or 0), 2),
        'balanceAfter': round(float(item.get('balance_after') or 0), 2),
        'creator': item.get('creator') or '',
        'remark': item.get('remark') or '',
        'attachmentUrl': item.get('attachment_url') or '',
        'status': item.get('status') or 'draft',
        'accountTransactionId': item.get('account_transaction_id'),
        'auditedBy': item.get('audited_by') or '',
        'auditedAt': item.get('audited_at') or '',
        'createdAt': item.get('created_at') or '',
        'updatedAt': item.get('updated_at') or '',
    }


def _validate_values(conn, data):
    try:
        customer_id = int(data.get('customerId'))
    except (TypeError, ValueError):
        raise ValueError('请选择客户')

    customer = conn.execute(
        '''
        SELECT id, customer_name, store_id, balance, receivable, status
        FROM customers
        WHERE id = ?
        ''',
        (customer_id,)
    ).fetchone()
    if not customer:
        raise ValueError('所选客户不存在')
    if customer['status'] != 'active':
        raise ValueError('所选客户已停用')
    if customer['store_id'] is None:
        raise ValueError('所选客户尚未关联门店')

    store = conn.execute(
        'SELECT id, name, status FROM stores WHERE id = ?',
        (customer['store_id'],)
    ).fetchone()
    if not store:
        raise ValueError('客户关联的门店不存在')
    if store['status'] != 'active':
        raise ValueError('客户关联的门店已停用')

    payment_amount = _money(data.get('paymentAmount'), '收款金额')
    discount_amount = _money(data.get('discountAmount'), '优惠金额')
    if payment_amount <= 0:
        raise ValueError('收款金额必须大于0')
    if discount_amount < 0:
        raise ValueError('优惠金额不能小于0')

    debt_before = max(_money(customer['receivable']), Decimal('0.00'))
    balance_before = _money(customer['balance'])
    if discount_amount > debt_before:
        raise ValueError('优惠金额不能超过客户当前欠款')

    cash_writeoff = min(payment_amount, debt_before - discount_amount)
    writeoff_amount = discount_amount + cash_writeoff
    advance_amount = payment_amount - cash_writeoff

    return {
        'document_date': _date(data.get('documentDate')),
        'store_id': store['id'],
        'customer_id': customer['id'],
        'settlement_account': f"{store['name']}结算账户",
        'payment_method': str(data.get('paymentMethod') or '').strip(),
        'payment_amount': payment_amount,
        'discount_amount': discount_amount,
        'total_amount': payment_amount + discount_amount,
        'writeoff_amount': writeoff_amount,
        'advance_amount': advance_amount,
        'debt_before': debt_before,
        'debt_after': debt_before - writeoff_amount,
        'balance_before': balance_before,
        'balance_after': balance_before + advance_amount,
        'creator': str(data.get('creator') or '王醒').strip() or '王醒',
        'remark': str(data.get('remark') or '').strip(),
        'attachment_url': str(data.get('attachmentUrl') or '').strip(),
    }


def _remove_attachment(attachment_url):
    if not attachment_url.startswith('/uploads/payment-receipts/'):
        return
    relative_path = attachment_url.removeprefix('/uploads/')
    upload_root = os.path.abspath(BASE_UPLOAD_DIR)
    target = os.path.abspath(os.path.join(upload_root, relative_path))
    try:
        if os.path.commonpath([upload_root, target]) != upload_root:
            return
    except ValueError:
        return
    if os.path.isfile(target):
        os.remove(target)


@payment_receipts_bp.route('', methods=['GET'])
def list_payment_receipts():
    store_id = request.args.get('storeId', type=int)
    status = str(request.args.get('status') or '').strip()
    keyword = str(request.args.get('keyword') or '').strip().lower()

    with get_db() as conn:
        sql = '''
            SELECT
                p.*,
                c.customer_code,
                c.customer_name,
                c.contact_person,
                c.phone,
                s.name AS store_name
            FROM payment_receipts p
            JOIN customers c ON c.id = p.customer_id
            LEFT JOIN stores s ON s.id = p.store_id
            WHERE 1 = 1
        '''
        params = []
        if store_id is not None:
            sql += ' AND p.store_id = ?'
            params.append(store_id)
        if status in {'draft', 'audited'}:
            sql += ' AND p.status = ?'
            params.append(status)
        sql += ' ORDER BY p.document_date DESC, p.id DESC'
        rows = conn.execute(sql, params).fetchall()

    items = [_serialize(row) for row in rows]
    if keyword:
        items = [
            item for item in items
            if keyword in ' '.join([
                item['documentNo'],
                item['customerCode'],
                item['customerName'],
                item['creator'],
                item['remark'],
            ]).lower()
        ]
    return jsonify({'items': items, 'total': len(items)})


@payment_receipts_bp.route('/next-number', methods=['GET'])
def next_payment_number():
    try:
        document_date = _date(
            request.args.get('date') or datetime.now().strftime('%Y-%m-%d')
        )
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    with get_db() as conn:
        document_no = _next_document_no(conn, document_date)
    return jsonify({'documentNo': document_no})


@payment_receipts_bp.route('/attachments', methods=['POST'])
def upload_attachment():
    file = request.files.get('attachment')
    if not file or not file.filename:
        return jsonify({'error': '请选择附件图片'}), 400
    if request.content_length and request.content_length > 10 * 1024 * 1024:
        return jsonify({'error': '附件图片不能超过10MB'}), 413

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'error': '附件仅支持jpg、png、webp或gif图片'}), 400

    month = datetime.now().strftime('%Y-%m')
    target_dir = os.path.join(BASE_UPLOAD_DIR, 'payment-receipts', month)
    os.makedirs(target_dir, exist_ok=True)
    filename = f"payment_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{extension}"
    file.save(os.path.join(target_dir, filename))
    return jsonify({
        'success': True,
        'attachmentUrl': f'/uploads/payment-receipts/{month}/{filename}'
    })


@payment_receipts_bp.route('', methods=['POST'])
def create_payment_receipt():
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                values = _validate_values(conn, data)
                document_no = _next_document_no(conn, values['document_date'])
                now = datetime.now().isoformat(timespec='seconds')
                cursor = conn.execute(
                    '''
                    INSERT INTO payment_receipts (
                        document_no, document_date, store_id, customer_id,
                        settlement_account, payment_method, payment_amount,
                        discount_amount, total_amount, writeoff_amount,
                        advance_amount, debt_before, debt_after,
                        balance_before, balance_after, creator, remark,
                        attachment_url, status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, 'draft', ?, ?)
                    ''',
                    (
                        document_no,
                        values['document_date'],
                        values['store_id'],
                        values['customer_id'],
                        values['settlement_account'],
                        values['payment_method'],
                        float(values['payment_amount']),
                        float(values['discount_amount']),
                        float(values['total_amount']),
                        float(values['writeoff_amount']),
                        float(values['advance_amount']),
                        float(values['debt_before']),
                        float(values['debt_after']),
                        float(values['balance_before']),
                        float(values['balance_after']),
                        values['creator'],
                        values['remark'],
                        values['attachment_url'],
                        now,
                        now,
                    )
                )
                receipt = _serialize(_receipt_row(conn, cursor.lastrowid))
        return jsonify({
            'success': True,
            'message': '收款单已保存，等待审核入账',
            'receipt': receipt
        }), 201
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        return jsonify({'error': f'保存收款单失败：{error}'}), 500


@payment_receipts_bp.route('/<int:receipt_id>', methods=['PUT'])
def update_payment_receipt(receipt_id):
    data = request.get_json(silent=True) or {}
    old_attachment_url = ''
    new_attachment_url = ''
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                existing = conn.execute(
                    'SELECT * FROM payment_receipts WHERE id = ?',
                    (receipt_id,)
                ).fetchone()
                if not existing:
                    return jsonify({'error': '收款单不存在'}), 404
                if existing['status'] != 'draft':
                    return jsonify({'error': '已审核收款单不能修改，请先反审核'}), 409
                old_attachment_url = existing['attachment_url'] or ''

                merged = {
                    'customerId': data.get('customerId', existing['customer_id']),
                    'documentDate': data.get(
                        'documentDate',
                        existing['document_date']
                    ),
                    'settlementAccount': data.get(
                        'settlementAccount',
                        existing['settlement_account']
                    ),
                    'paymentMethod': data.get(
                        'paymentMethod',
                        existing['payment_method']
                    ),
                    'paymentAmount': data.get(
                        'paymentAmount',
                        existing['payment_amount']
                    ),
                    'discountAmount': data.get(
                        'discountAmount',
                        existing['discount_amount']
                    ),
                    'creator': data.get('creator', existing['creator']),
                    'remark': data.get('remark', existing['remark']),
                    'attachmentUrl': data.get(
                        'attachmentUrl',
                        existing['attachment_url']
                    ),
                }
                values = _validate_values(conn, merged)
                new_attachment_url = values['attachment_url']
                now = datetime.now().isoformat(timespec='seconds')
                conn.execute(
                    '''
                    UPDATE payment_receipts
                    SET document_date = ?, store_id = ?, customer_id = ?,
                        settlement_account = ?, payment_method = ?,
                        payment_amount = ?, discount_amount = ?,
                        total_amount = ?, writeoff_amount = ?,
                        advance_amount = ?, debt_before = ?, debt_after = ?,
                        balance_before = ?, balance_after = ?, creator = ?,
                        remark = ?, attachment_url = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        values['document_date'],
                        values['store_id'],
                        values['customer_id'],
                        values['settlement_account'],
                        values['payment_method'],
                        float(values['payment_amount']),
                        float(values['discount_amount']),
                        float(values['total_amount']),
                        float(values['writeoff_amount']),
                        float(values['advance_amount']),
                        float(values['debt_before']),
                        float(values['debt_after']),
                        float(values['balance_before']),
                        float(values['balance_after']),
                        values['creator'],
                        values['remark'],
                        values['attachment_url'],
                        now,
                        receipt_id,
                    )
                )
                receipt = _serialize(_receipt_row(conn, receipt_id))
        if (
            old_attachment_url
            and old_attachment_url != new_attachment_url
        ):
            try:
                _remove_attachment(old_attachment_url)
            except OSError:
                pass
        return jsonify({
            'success': True,
            'message': '收款单修改成功',
            'receipt': receipt
        })
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        return jsonify({'error': f'修改收款单失败：{error}'}), 500


@payment_receipts_bp.route('/<int:receipt_id>', methods=['DELETE'])
def delete_payment_receipt(receipt_id):
    attachment_url = ''
    with _write_lock:
        with get_db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            receipt = conn.execute(
                'SELECT status, attachment_url FROM payment_receipts WHERE id = ?',
                (receipt_id,)
            ).fetchone()
            if not receipt:
                return jsonify({'error': '收款单不存在'}), 404
            if receipt['status'] != 'draft':
                return jsonify({'error': '已审核收款单不能删除，请先反审核'}), 409
            attachment_url = receipt['attachment_url'] or ''
            conn.execute('DELETE FROM payment_receipts WHERE id = ?', (receipt_id,))
    try:
        _remove_attachment(attachment_url)
    except OSError:
        pass
    return jsonify({'success': True, 'message': '收款单已删除'})


@payment_receipts_bp.route('/<int:receipt_id>/audit', methods=['POST'])
def audit_payment_receipt(receipt_id):
    now = datetime.now().isoformat(timespec='seconds')
    operator = _operator()
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                receipt = conn.execute(
                    'SELECT * FROM payment_receipts WHERE id = ?',
                    (receipt_id,)
                ).fetchone()
                if not receipt:
                    return jsonify({'error': '收款单不存在'}), 404
                if receipt['status'] == 'audited':
                    return jsonify({'error': '收款单已经审核，请勿重复操作'}), 409

                customer = conn.execute(
                    '''
                    SELECT id, customer_name, balance, receivable
                    FROM customers
                    WHERE id = ?
                    ''',
                    (receipt['customer_id'],)
                ).fetchone()
                if not customer:
                    return jsonify({'error': '收款单关联的客户不存在'}), 409

                active = conn.execute(
                    '''
                    SELECT id
                    FROM customer_account_transactions
                    WHERE payment_id = ?
                      AND transaction_type = 'customer_payment'
                      AND status = 'active'
                    ''',
                    (receipt_id,)
                ).fetchone()
                if active:
                    return jsonify({'error': '该收款单已有有效入账流水'}), 409

                debt_before = max(_money(customer['receivable']), Decimal('0.00'))
                balance_before = _money(customer['balance'])
                payment_amount = _money(receipt['payment_amount'])
                discount_amount = _money(receipt['discount_amount'])
                if discount_amount > debt_before:
                    return jsonify({
                        'error': '客户当前欠款已发生变化，优惠金额不能超过当前欠款，请修改后再审核'
                    }), 409

                cash_writeoff = min(
                    payment_amount,
                    debt_before - discount_amount
                )
                writeoff_amount = discount_amount + cash_writeoff
                advance_amount = payment_amount - cash_writeoff
                debt_after = debt_before - writeoff_amount
                balance_after = balance_before + advance_amount

                conn.execute(
                    '''
                    UPDATE customers
                    SET balance = ?, receivable = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        float(balance_after),
                        float(debt_after),
                        now,
                        customer['id'],
                    )
                )
                transaction_cursor = conn.execute(
                    '''
                    INSERT INTO customer_account_transactions (
                        customer_id, payment_id, payment_number,
                        transaction_type, debt_recovered, discount_amount,
                        balance_change, receivable_change,
                        balance_after, receivable_after,
                        status, operator, created_at
                    )
                    VALUES (?, ?, ?, 'customer_payment', ?, ?, ?, ?, ?, ?,
                            'active', ?, ?)
                    ''',
                    (
                        customer['id'],
                        receipt_id,
                        receipt['document_no'],
                        float(cash_writeoff),
                        float(discount_amount),
                        float(advance_amount),
                        float(-writeoff_amount),
                        float(balance_after),
                        float(debt_after),
                        operator,
                        now,
                    )
                )
                conn.execute(
                    '''
                    UPDATE payment_receipts
                    SET writeoff_amount = ?, advance_amount = ?,
                        debt_before = ?, debt_after = ?,
                        balance_before = ?, balance_after = ?,
                        status = 'audited', account_transaction_id = ?,
                        audited_by = ?, audited_at = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        float(writeoff_amount),
                        float(advance_amount),
                        float(debt_before),
                        float(debt_after),
                        float(balance_before),
                        float(balance_after),
                        transaction_cursor.lastrowid,
                        operator,
                        now,
                        now,
                        receipt_id,
                    )
                )
                result = _serialize(_receipt_row(conn, receipt_id))
        return jsonify({
            'success': True,
            'message': (
                f"审核入账成功：核销欠款{float(writeoff_amount):.2f}元，"
                f"转入预收{float(advance_amount):.2f}元"
            ),
            'receipt': result,
        })
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        return jsonify({'error': f'审核收款单失败：{error}'}), 500


@payment_receipts_bp.route('/<int:receipt_id>/audit', methods=['DELETE'])
def reverse_payment_receipt(receipt_id):
    now = datetime.now().isoformat(timespec='seconds')
    operator = _operator()
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                receipt = conn.execute(
                    'SELECT * FROM payment_receipts WHERE id = ?',
                    (receipt_id,)
                ).fetchone()
                if not receipt:
                    return jsonify({'error': '收款单不存在'}), 404
                if receipt['status'] != 'audited':
                    return jsonify({'error': '收款单尚未审核'}), 409

                transaction = conn.execute(
                    '''
                    SELECT *
                    FROM customer_account_transactions
                    WHERE id = ?
                      AND payment_id = ?
                      AND transaction_type = 'customer_payment'
                      AND status = 'active'
                    ''',
                    (receipt['account_transaction_id'], receipt_id)
                ).fetchone()
                if not transaction:
                    return jsonify({'error': '找不到该收款单的有效入账流水'}), 409

                customer = conn.execute(
                    '''
                    SELECT id, customer_name, balance, receivable
                    FROM customers
                    WHERE id = ?
                    ''',
                    (transaction['customer_id'],)
                ).fetchone()
                if not customer:
                    return jsonify({'error': '入账流水关联的客户不存在'}), 409

                balance_before = _money(customer['balance'])
                receivable_before = _money(customer['receivable'])
                advance_amount = max(
                    _money(transaction['balance_change']),
                    Decimal('0.00')
                )
                writeoff_amount = max(
                    -_money(transaction['receivable_change']),
                    Decimal('0.00')
                )
                if balance_before < advance_amount:
                    return jsonify({
                        'error': '本单产生的预收款已被后续订单使用，不能直接反审核'
                    }), 409

                balance_after = balance_before - advance_amount
                receivable_after = receivable_before + writeoff_amount
                conn.execute(
                    '''
                    UPDATE customers
                    SET balance = ?, receivable = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        float(balance_after),
                        float(receivable_after),
                        now,
                        customer['id'],
                    )
                )
                conn.execute(
                    '''
                    UPDATE customer_account_transactions
                    SET status = 'reversed', reversed_at = ?
                    WHERE id = ?
                    ''',
                    (now, transaction['id'])
                )
                conn.execute(
                    '''
                    INSERT INTO customer_account_transactions (
                        customer_id, payment_id, payment_number,
                        transaction_type, source_transaction_id,
                        balance_change, receivable_change,
                        balance_after, receivable_after,
                        status, operator, created_at
                    )
                    VALUES (?, ?, ?, 'customer_payment_reverse', ?, ?, ?, ?, ?,
                            'active', ?, ?)
                    ''',
                    (
                        customer['id'],
                        receipt_id,
                        receipt['document_no'],
                        transaction['id'],
                        float(-advance_amount),
                        float(writeoff_amount),
                        float(balance_after),
                        float(receivable_after),
                        operator,
                        now,
                    )
                )

                payment_amount = _money(receipt['payment_amount'])
                discount_amount = _money(receipt['discount_amount'])
                preview_cash = min(
                    payment_amount,
                    max(
                        Decimal('0.00'),
                        receivable_after - discount_amount
                    )
                )
                preview_writeoff = min(
                    receivable_after,
                    discount_amount + preview_cash
                )
                preview_advance = payment_amount - preview_cash
                conn.execute(
                    '''
                    UPDATE payment_receipts
                    SET status = 'draft', account_transaction_id = NULL,
                        audited_by = NULL, audited_at = NULL,
                        writeoff_amount = ?, advance_amount = ?,
                        debt_before = ?, debt_after = ?,
                        balance_before = ?, balance_after = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        float(preview_writeoff),
                        float(preview_advance),
                        float(receivable_after),
                        float(receivable_after - preview_writeoff),
                        float(balance_after),
                        float(balance_after + preview_advance),
                        now,
                        receipt_id,
                    )
                )
                result = _serialize(_receipt_row(conn, receipt_id))
        return jsonify({
            'success': True,
            'message': '反审核成功，客户欠款与储值余额已恢复',
            'receipt': result,
        })
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        return jsonify({'error': f'反审核收款单失败：{error}'}), 500
