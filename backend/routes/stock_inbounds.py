"""Stock-in documents, suppliers and inventory posting APIs.

The legacy product inventory endpoint is intentionally left intact.  These
routes provide a document-oriented write path so drafts do not change stock
and a posted document can be audited/replayed from its movement rows.
"""

import json
import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, jsonify, request

from utils.db import get_db


stock_inbounds_bp = Blueprint(
    'stock_inbounds',
    __name__,
    url_prefix='/api',
)

_write_lock = threading.Lock()
_MONEY_QUANT = Decimal('0.01')


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _number(value, default=Decimal('0')):
    if value is None or value == '':
        return default
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('数值格式不正确')
    if not number.is_finite():
        raise ValueError('数值必须是有限数字')
    return number


def _optional_int(value, field):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field}必须是整数')


def _required_int(value, field):
    parsed = _optional_int(value, field)
    if parsed is None:
        raise ValueError(f'请选择{field}')
    return parsed


def _type(value):
    text = str(value or '').strip().lower()
    if text in ('finished', 'finished-product', 'product', 'goods'):
        return 'finished-product'
    if text in ('raw', 'raw-material', 'material', 'materials'):
        return 'raw-material'
    raise ValueError('入库类型无效')


def _status(value):
    text = str(value or 'draft').strip().lower()
    if text not in ('draft', 'posted', 'cancelled'):
        raise ValueError('单据状态无效')
    return text


def _clean_text(value, max_length=None):
    text = '' if value is None else str(value).strip()
    return text[:max_length] if max_length else text


def _supplier_response(row):
    if not row:
        return None
    supplier = dict(row)
    supplier['supplierCode'] = supplier.pop('supplier_code', '') or ''
    supplier['supplierName'] = supplier.pop('supplier_name', '') or ''
    supplier['storeId'] = supplier.pop('store_id', None)
    supplier['contactPerson'] = supplier.pop('contact_person', '') or ''
    supplier['taxNumber'] = supplier.pop('tax_number', '') or ''
    supplier['bankName'] = supplier.pop('bank_name', '') or ''
    supplier['bankAccount'] = supplier.pop('bank_account', '') or ''
    supplier['createdAt'] = supplier.pop('created_at', '') or ''
    supplier['updatedAt'] = supplier.pop('updated_at', '') or ''
    return supplier


def _supplier_payload(data, existing=None):
    existing = existing or {}
    name = _clean_text(data.get('name', data.get('supplierName', existing.get('supplier_name', existing.get('supplierName', '')))), 120)
    if not name:
        raise ValueError('供应商名称不能为空')
    code = _clean_text(data.get('code', data.get('supplierCode', existing.get('supplier_code', existing.get('supplierCode', '')))), 60)
    return {
        'supplier_code': code,
        'supplier_name': name,
        'store_id': _optional_int(data.get('storeId', existing.get('store_id', existing.get('storeId'))), '门店ID'),
        'contact_person': _clean_text(data.get('contactPerson', existing.get('contact_person', existing.get('contactPerson', ''))), 80),
        'phone': _clean_text(data.get('phone', existing.get('phone', '')), 40),
        'address': _clean_text(data.get('address', existing.get('address', '')), 240),
        'tax_number': _clean_text(data.get('taxNumber', existing.get('tax_number', existing.get('taxNumber', ''))), 80),
        'bank_name': _clean_text(data.get('bankName', existing.get('bank_name', existing.get('bankName', ''))), 120),
        'bank_account': _clean_text(data.get('bankAccount', existing.get('bank_account', existing.get('bankAccount', ''))), 120),
        'remark': _clean_text(data.get('remark', existing.get('remark', '')), 500),
        'status': _clean_text(data.get('status', existing.get('status', 'active')), 20) or 'active',
    }


@stock_inbounds_bp.route('/suppliers', methods=['GET'])
def list_suppliers():
    store_id = request.args.get('storeId', type=int)
    status = _clean_text(request.args.get('status'))
    with get_db() as conn:
        sql = 'SELECT * FROM suppliers WHERE 1 = 1'
        params = []
        if store_id is not None:
            sql += ' AND (store_id = ? OR store_id IS NULL)'
            params.append(store_id)
        if status:
            sql += ' AND status = ?'
            params.append(status)
        sql += ' ORDER BY supplier_name COLLATE NOCASE, id'
        rows = conn.execute(sql, params).fetchall()
        return jsonify([_supplier_response(row) for row in rows])


@stock_inbounds_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    data = request.get_json(silent=True) or {}
    try:
        values = _supplier_payload(data)
        now = _now()
        with get_db() as conn:
            if values['supplier_code']:
                duplicate = conn.execute(
                    'SELECT 1 FROM suppliers WHERE supplier_code = ?',
                    (values['supplier_code'],),
                ).fetchone()
                if duplicate:
                    return jsonify({'success': False, 'message': '供应商编号已存在'}), 409
            cursor = conn.execute(
                '''
                INSERT INTO suppliers (
                    supplier_code, supplier_name, store_id, contact_person,
                    phone, address, tax_number, bank_name, bank_account,
                    remark, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    values['supplier_code'], values['supplier_name'], values['store_id'],
                    values['contact_person'], values['phone'], values['address'],
                    values['tax_number'], values['bank_name'], values['bank_account'],
                    values['remark'], values['status'], now, now,
                ),
            )
            row = conn.execute('SELECT * FROM suppliers WHERE id = ?', (cursor.lastrowid,)).fetchone()
            return jsonify({'success': True, 'supplier': _supplier_response(row)}), 201
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@stock_inbounds_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    data = request.get_json(silent=True) or {}
    try:
        with get_db() as conn:
            existing_row = conn.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,)).fetchone()
            if not existing_row:
                return jsonify({'success': False, 'message': '供应商不存在'}), 404
            values = _supplier_payload(data, dict(existing_row))
            if values['supplier_code']:
                duplicate = conn.execute(
                    'SELECT 1 FROM suppliers WHERE supplier_code = ? AND id <> ?',
                    (values['supplier_code'], supplier_id),
                ).fetchone()
                if duplicate:
                    return jsonify({'success': False, 'message': '供应商编号已存在'}), 409
            conn.execute(
                '''
                UPDATE suppliers SET supplier_code = ?, supplier_name = ?, store_id = ?,
                    contact_person = ?, phone = ?, address = ?, tax_number = ?,
                    bank_name = ?, bank_account = ?, remark = ?, status = ?, updated_at = ?
                WHERE id = ?
                ''',
                (
                    values['supplier_code'], values['supplier_name'], values['store_id'],
                    values['contact_person'], values['phone'], values['address'],
                    values['tax_number'], values['bank_name'], values['bank_account'],
                    values['remark'], values['status'], _now(), supplier_id,
                ),
            )
            row = conn.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,)).fetchone()
            return jsonify({'success': True, 'supplier': _supplier_response(row)})
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@stock_inbounds_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    with get_db() as conn:
        used = conn.execute('SELECT 1 FROM stock_inbounds WHERE supplier_id = ? LIMIT 1', (supplier_id,)).fetchone()
        if used:
            conn.execute("UPDATE suppliers SET status = 'inactive', updated_at = ? WHERE id = ?", (_now(), supplier_id))
            return jsonify({'success': True, 'message': '供应商已停用'})
        cursor = conn.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '供应商不存在'}), 404
        return jsonify({'success': True, 'message': '删除成功'})


def _product_exists(conn, receipt_type, product_id):
    if product_id is None:
        return True
    table = 'raw_material_products' if receipt_type == 'raw-material' else 'products'
    return conn.execute(f'SELECT 1 FROM {table} WHERE id = ?', (product_id,)).fetchone() is not None


def _normalize_items(conn, receipt_type, raw_items, require_valid=False):
    if raw_items is None:
        raw_items = []
    if not isinstance(raw_items, list):
        raise ValueError('明细必须是数组')

    normalized = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        product_id = _optional_int(raw.get('productId', raw.get('product_id')), '物料ID')
        name = _clean_text(raw.get('name', raw.get('productName', raw.get('product_name', ''))), 160)
        received = _number(raw.get('receivedQty', raw.get('received_qty', raw.get('quantity'))), Decimal('0'))
        expected = _number(raw.get('expectedQty', raw.get('expected_qty')), Decimal('0'))
        price_value = raw.get('unitPrice', raw.get('unit_price', raw.get('price')))
        price = None if price_value in (None, '') else _number(price_value)
        tax_rate = _number(raw.get('taxRate', raw.get('tax_rate', 0)), Decimal('0'))
        if tax_rate < 0 or tax_rate > 100:
            raise ValueError('税率必须在 0 到 100 之间')
        tax_amount = (received * (price or Decimal('0')) * tax_rate / Decimal('100')).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
        total_amount = (received * (price or Decimal('0')) + tax_amount).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)

        has_any = product_id is not None or name or received != 0 or raw.get('batchNo', raw.get('batch_no'))
        if not has_any:
            continue
        if product_id is None and not name:
            raise ValueError('每条明细必须选择物料')
        if product_id is not None and not _product_exists(conn, receipt_type, product_id):
            raise ValueError(f'物料 ID {product_id} 不存在')
        if require_valid and received <= 0:
            raise ValueError('实收数量必须大于 0')
        batch_no = _clean_text(raw.get('batchNo', raw.get('batch_no', '')), 80)
        if require_valid and not batch_no:
            raise ValueError('批次号不能为空')

        normalized.append({
            'product_id': product_id,
            'product_code': _clean_text(raw.get('code', raw.get('productCode', raw.get('product_code', ''))), 80),
            'product_name': name,
            'specification': _clean_text(raw.get('specification', raw.get('spec', '')), 180),
            'unit': _clean_text(raw.get('unit', raw.get('unitName', '')), 40),
            'expected_qty': float(expected) if raw.get('expectedQty', raw.get('expected_qty')) not in (None, '') else None,
            'received_qty': float(received),
            'bin_code': _clean_text(raw.get('binCode', raw.get('bin_code', '')), 80),
            'batch_no': batch_no,
            'unit_price': float(price) if price is not None else None,
            'tax_rate': float(tax_rate),
            'tax_amount': float(tax_amount),
            'total_amount': float(total_amount),
            'remark': _clean_text(raw.get('remark', ''), 500),
        })
    if require_valid and not normalized:
        raise ValueError('提交过账至少需要 1 条有效物料明细')
    return normalized


def _document_values(conn, data, existing=None, for_post=False):
    existing = existing or {}
    receipt_type = _type(data.get('type', data.get('receiptType', existing.get('receipt_type'))))
    status = _status(data.get('status', existing.get('status', 'draft')))
    if for_post:
        status = 'posted'
    document_date = _clean_text(data.get('documentDate', data.get('document_date', existing.get('document_date', ''))), 20)
    if not document_date:
        raise ValueError('请选择单据日期')
    warehouse_id = _required_int(data.get('warehouseId', data.get('warehouse_id', existing.get('warehouse_id'))), '目标仓库')
    store_id = _optional_int(data.get('storeId', data.get('store_id', existing.get('store_id'))), '门店ID')
    supplier_id = _optional_int(data.get('supplierId', data.get('supplier_id', existing.get('supplier_id'))), '供应商ID')
    workshop = _clean_text(data.get('workshop', data.get('productionWorkshop', existing.get('workshop', ''))), 80)
    if receipt_type == 'raw-material' and for_post:
        if supplier_id is None:
            raise ValueError('请选择供应商')
        if not conn.execute("SELECT 1 FROM suppliers WHERE id = ? AND status = 'active'", (supplier_id,)).fetchone():
            raise ValueError('供应商不存在或已停用')
    if not conn.execute('SELECT 1 FROM warehouses WHERE id = ?', (warehouse_id,)).fetchone():
        raise ValueError('目标仓库不存在')
    items = _normalize_items(conn, receipt_type, data.get('items', existing.get('_items', [])), for_post)
    if for_post and not any(item['received_qty'] > 0 for item in items):
        raise ValueError('提交过账至少需要 1 条有效物料明细')
    total_quantity = sum(Decimal(str(item['received_qty'])) for item in items)
    total_tax = sum(Decimal(str(item['tax_amount'])) for item in items).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    total_amount = sum(Decimal(str(item['total_amount'])) for item in items).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    return {
        'document_no': _clean_text(data.get('documentNo', data.get('document_no', existing.get('document_no', ''))), 80),
        'document_date': document_date,
        'receipt_type': receipt_type,
        'store_id': store_id,
        'warehouse_id': warehouse_id,
        'supplier_id': supplier_id if receipt_type == 'raw-material' else None,
        'workshop': workshop if receipt_type == 'finished-product' else '',
        'inspector': _clean_text(data.get('inspector', existing.get('inspector', '')), 80),
        'quality_no': _clean_text(data.get('qualityNo', data.get('quality_no', existing.get('quality_no', ''))), 80),
        'remark': _clean_text(data.get('remark', existing.get('remark', '')), 200),
        'attachments': data.get('attachments', existing.get('attachments', [])) or [],
        'status': status,
        'items': items,
        'total_quantity': float(total_quantity),
        'total_tax': float(total_tax),
        'total_amount': float(total_amount),
    }


def _serialize_item(row):
    item = dict(row)
    item['productId'] = item.pop('product_id', None)
    item['productCode'] = item.pop('product_code', '') or ''
    item['productName'] = item.pop('product_name', '') or ''
    item['expectedQty'] = item.pop('expected_qty', None)
    item['receivedQty'] = item.pop('received_qty', 0)
    item['binCode'] = item.pop('bin_code', '') or ''
    item['batchNo'] = item.pop('batch_no', '') or ''
    item['unitPrice'] = item.pop('unit_price', None)
    item['taxRate'] = item.pop('tax_rate', 0)
    item['taxAmount'] = item.pop('tax_amount', 0)
    item['totalAmount'] = item.pop('total_amount', 0)
    return item


def _serialize_document(conn, row, include_items=True):
    document = dict(row)
    document['documentNo'] = document.pop('document_no', '')
    document['documentDate'] = document.pop('document_date', '')
    document['type'] = document.pop('receipt_type', '')
    document['storeId'] = document.pop('store_id', None)
    document['warehouseId'] = document.pop('warehouse_id', None)
    document['supplierId'] = document.pop('supplier_id', None)
    document['qualityNo'] = document.pop('quality_no', '') or ''
    document['totalQuantity'] = document.pop('total_quantity', 0)
    document['totalTax'] = document.pop('total_tax', 0)
    document['totalAmount'] = document.pop('total_amount', 0)
    document['postedAt'] = document.pop('posted_at', None)
    document['createdAt'] = document.pop('created_at', '')
    document['updatedAt'] = document.pop('updated_at', '')
    try:
        document['attachments'] = json.loads(document.get('attachments') or '[]')
    except (TypeError, ValueError):
        document['attachments'] = []
    if include_items:
        items = conn.execute(
            'SELECT * FROM stock_inbound_items WHERE inbound_id = ? ORDER BY line_no, id',
            (row['id'],),
        ).fetchall()
        document['items'] = [_serialize_item(item) for item in items]
    return document


def _post_items(conn, document_row, item_rows):
    """Apply a posted document in the caller's transaction."""
    receipt_type = document_row['receipt_type']
    now = _now()
    for item in item_rows:
        qty = float(item['received_qty'] or 0)
        if qty <= 0 or item['product_id'] is None:
            continue
        product_id = int(item['product_id'])
        warehouse_id = int(document_row['warehouse_id'] or 0)
        store_id = int(document_row['store_id'] or 0)
        bin_code = item['bin_code'] or ''
        batch_no = item['batch_no'] or ''
        conn.execute(
            '''
            INSERT INTO stock_balances (
                product_type, product_id, warehouse_id, store_id,
                bin_code, batch_no, quantity, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_type, product_id, warehouse_id, store_id, bin_code, batch_no)
            DO UPDATE SET quantity = stock_balances.quantity + excluded.quantity,
                          updated_at = excluded.updated_at
            ''',
            (receipt_type, product_id, warehouse_id, store_id, bin_code, batch_no, qty, now),
        )
        conn.execute(
            '''
            INSERT INTO stock_movements (
                movement_type, receipt_type, source_document_id, source_document_no,
                source_item_id, product_type, product_id, warehouse_id, store_id,
                bin_code, batch_no, quantity, unit_price, tax_rate, total_amount, created_at
            ) VALUES ('in', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                receipt_type, document_row['id'], document_row['document_no'], item['id'],
                receipt_type, product_id, warehouse_id, store_id, bin_code, batch_no,
                qty, item['unit_price'], item['tax_rate'], item['total_amount'], now,
            ),
        )
        if receipt_type == 'finished-product':
            # Keep the legacy product inventory endpoint/data in sync.
            conn.execute(
                '''
                INSERT INTO inventory (product_id, stock, min_stock, max_stock, updated_at)
                VALUES (?, ?, 0, 0, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    stock = COALESCE(inventory.stock, 0) + excluded.stock,
                    updated_at = excluded.updated_at
                ''',
                (product_id, qty, now),
            )


def _insert_items(conn, inbound_id, receipt_type, items):
    for line_no, item in enumerate(items, start=1):
        cursor = conn.execute(
            '''
            INSERT INTO stock_inbound_items (
                inbound_id, line_no, product_type, product_id, product_code,
                product_name, specification, unit, expected_qty, received_qty,
                bin_code, batch_no, unit_price, tax_rate, tax_amount,
                total_amount, remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                inbound_id, line_no, receipt_type, item['product_id'], item['product_code'],
                item['product_name'], item['specification'], item['unit'], item['expected_qty'],
                item['received_qty'], item['bin_code'], item['batch_no'], item['unit_price'],
                item['tax_rate'], item['tax_amount'], item['total_amount'], item['remark'],
            ),
        )
        item['id'] = cursor.lastrowid


def _document_insert(conn, values):
    now = _now()
    cursor = conn.execute(
        '''
        INSERT INTO stock_inbounds (
            document_no, document_date, receipt_type, store_id, warehouse_id,
            supplier_id, workshop, inspector, quality_no, remark, attachments,
            status, total_quantity, total_tax, total_amount, posted_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            values['document_no'] or f'TEMP-{now.replace(" ", "").replace(":", "").replace("-", "")}-{threading.get_ident()}',
            values['document_date'], values['receipt_type'], values['store_id'], values['warehouse_id'],
            values['supplier_id'], values['workshop'], values['inspector'], values['quality_no'],
            values['remark'], json.dumps(values['attachments'], ensure_ascii=False), values['status'],
            values['total_quantity'], values['total_tax'], values['total_amount'],
            now if values['status'] == 'posted' else None, now, now,
        ),
    )
    inbound_id = cursor.lastrowid
    if not values['document_no']:
        generated = f"RK{values['document_date'].replace('-', '')[:8]}{inbound_id:03d}"
        conn.execute('UPDATE stock_inbounds SET document_no = ? WHERE id = ?', (generated, inbound_id))
    row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
    _insert_items(conn, inbound_id, values['receipt_type'], values['items'])
    if values['status'] == 'posted':
        _post_items(conn, row, [dict(item, id=item.get('id')) for item in values['items']])
    return conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()


def _existing_values(conn, inbound_id):
    row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
    if not row:
        return None, None
    items = conn.execute('SELECT * FROM stock_inbound_items WHERE inbound_id = ? ORDER BY line_no', (inbound_id,)).fetchall()
    values = dict(row)
    values['_items'] = [dict(item) for item in items]
    return row, values


@stock_inbounds_bp.route('/stock-inbounds', methods=['GET'])
def list_stock_inbounds():
    receipt_type = request.args.get('type')
    status = request.args.get('status')
    with get_db() as conn:
        sql = 'SELECT * FROM stock_inbounds WHERE 1 = 1'
        params = []
        if receipt_type:
            sql += ' AND receipt_type = ?'
            params.append(_type(receipt_type))
        if status:
            sql += ' AND status = ?'
            params.append(_status(status))
        sql += ' ORDER BY id DESC'
        rows = conn.execute(sql, params).fetchall()
        return jsonify([_serialize_document(conn, row) for row in rows])


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>', methods=['GET'])
def get_stock_inbound(inbound_id):
    with get_db() as conn:
        row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
        if not row:
            return jsonify({'success': False, 'message': '入库单不存在'}), 404
        return jsonify(_serialize_document(conn, row))


@stock_inbounds_bp.route('/stock-inbounds', methods=['POST'])
def create_stock_inbound():
    data = request.get_json(silent=True) or {}
    requested_status = str(data.get('status') or 'draft').lower()
    try:
        with _write_lock:
            with get_db() as conn:
                values = _document_values(conn, data, for_post=requested_status == 'posted')
                row = _document_insert(conn, values)
                return jsonify({'success': True, 'message': '入库单保存成功', 'stockIn': _serialize_document(conn, row), 'id': row['id']}), 201
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        # A duplicate user-supplied document number is a client error.
        if 'UNIQUE constraint failed: stock_inbounds.document_no' in str(exc):
            return jsonify({'success': False, 'message': '入库单号已存在'}), 409
        return jsonify({'success': False, 'message': '入库单保存失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>', methods=['PUT'])
def update_stock_inbound(inbound_id):
    data = request.get_json(silent=True) or {}
    requested_status = str(data.get('status') or '').lower()
    try:
        with _write_lock:
            with get_db() as conn:
                old_row, old_values = _existing_values(conn, inbound_id)
                if not old_row:
                    return jsonify({'success': False, 'message': '入库单不存在'}), 404
                if old_row['status'] == 'posted':
                    return jsonify({'success': False, 'message': '已过账单据不可修改'}), 409
                values = _document_values(conn, data, existing=old_values, for_post=requested_status == 'posted')
                now = _now()
                document_no = values['document_no'] or old_row['document_no']
                conn.execute(
                    '''
                    UPDATE stock_inbounds SET document_no = ?, document_date = ?, receipt_type = ?,
                        store_id = ?, warehouse_id = ?, supplier_id = ?, workshop = ?, inspector = ?,
                        quality_no = ?, remark = ?, attachments = ?, status = ?, total_quantity = ?,
                        total_tax = ?, total_amount = ?, posted_at = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        document_no, values['document_date'], values['receipt_type'], values['store_id'],
                        values['warehouse_id'], values['supplier_id'], values['workshop'], values['inspector'],
                        values['quality_no'], values['remark'], json.dumps(values['attachments'], ensure_ascii=False),
                        values['status'], values['total_quantity'], values['total_tax'], values['total_amount'],
                        now if values['status'] == 'posted' else None, now, inbound_id,
                    ),
                )
                conn.execute('DELETE FROM stock_inbound_items WHERE inbound_id = ?', (inbound_id,))
                _insert_items(conn, inbound_id, values['receipt_type'], values['items'])
                if values['status'] == 'posted':
                    new_row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                    _post_items(conn, new_row, [dict(item, id=item.get('id')) for item in values['items']])
                row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                return jsonify({'success': True, 'message': '入库单更新成功', 'stockIn': _serialize_document(conn, row)})
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        if 'UNIQUE constraint failed: stock_inbounds.document_no' in str(exc):
            return jsonify({'success': False, 'message': '入库单号已存在'}), 409
        return jsonify({'success': False, 'message': '入库单更新失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>', methods=['DELETE'])
def cancel_stock_inbound(inbound_id):
    with get_db() as conn:
        row = conn.execute('SELECT status FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
        if not row:
            return jsonify({'success': False, 'message': '入库单不存在'}), 404
        if row['status'] == 'posted':
            return jsonify({'success': False, 'message': '已过账单据不能直接删除'}), 409
        conn.execute("UPDATE stock_inbounds SET status = 'cancelled', updated_at = ? WHERE id = ?", (_now(), inbound_id))
        return jsonify({'success': True, 'message': '入库单已作废'})


@stock_inbounds_bp.route('/stock-balances', methods=['GET'])
def list_stock_balances():
    receipt_type = request.args.get('type')
    with get_db() as conn:
        sql = '''
            SELECT product_type, product_id, warehouse_id, store_id,
                   SUM(quantity) AS quantity, MAX(updated_at) AS updated_at
            FROM stock_balances WHERE 1 = 1
        '''
        params = []
        if receipt_type:
            sql += ' AND product_type = ?'
            params.append(_type(receipt_type))
        sql += ' GROUP BY product_type, product_id, warehouse_id, store_id ORDER BY product_id'
        rows = conn.execute(sql, params).fetchall()
        return jsonify([
            {
                'productType': row['product_type'],
                'productId': row['product_id'],
                'warehouseId': row['warehouse_id'],
                'storeId': row['store_id'],
                'quantity': row['quantity'] or 0,
                'updatedAt': row['updated_at'],
            }
            for row in rows
        ])
