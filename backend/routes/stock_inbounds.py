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
from utils.notifications import create_audit_notifications, complete_audit_notifications
from utils.auth import admin_permission_granted, require_admin_permission, current_identity
from utils.supplier_ledger import (
    FinanceError, balance, check_scope, check_version, idempotent_result,
    post_inbound_payables, reverse_inbound_payables, save_operation, source_summary,
)
from utils.permission_catalog import ADMIN_AUDIT_NOTIFICATION_PERMISSIONS, ADMIN_PURCHASE_ORDER_PERMISSIONS


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
    if text not in ('draft', 'reviewed', 'posted', 'cancelled'):
        raise ValueError('单据状态无效')
    return text


def _is_audited(status):
    """已审核单据才允许生成库存流水。posted 保留用于兼容旧数据。"""
    return str(status or '').lower() in ('reviewed', 'posted')


def _clean_text(value, max_length=None):
    text = '' if value is None else str(value).strip()
    return text[:max_length] if max_length else text


def _supplier_response(row, conn):
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
    supplier.pop('payable', None)
    supplier.update(balance(conn, row['id']))
    supplier['payable'] = supplier['payableBalance']
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
        return jsonify([_supplier_response(row, conn) for row in rows])


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
            return jsonify({'success': True, 'supplier': _supplier_response(row, conn)}), 201
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
            return jsonify({'success': True, 'supplier': _supplier_response(row, conn)})
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400


@stock_inbounds_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    with get_db() as conn:
        used = conn.execute(
            """SELECT 1 FROM stock_inbounds WHERE supplier_id = ?
               UNION ALL SELECT 1 FROM stock_inbound_items WHERE supplier_id = ?
               UNION ALL SELECT 1 FROM purchase_order_items WHERE supplier_id = ?
               UNION ALL SELECT 1 FROM supplier_account_transactions WHERE supplier_id = ?
               LIMIT 1""", (supplier_id,) * 4,
        ).fetchone()
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


def _normalize_items(conn, receipt_type, raw_items, require_valid=False, default_warehouse_id=None, allow_mixed_types=False):
    if raw_items is None:
        raw_items = []
    if not isinstance(raw_items, list):
        raise ValueError('明细必须是数组')

    normalized = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        product_id = _optional_int(raw.get('productId', raw.get('product_id')), '物料ID')
        product_type = _type(raw.get('productType', raw.get('product_type', receipt_type)))
        if not allow_mixed_types and product_type != receipt_type:
            raise ValueError('入库明细类型与单据类型不一致')
        purchase_order_item_id = _optional_int(
            raw.get('purchaseOrderItemId', raw.get('purchase_order_item_id')), 'purchase order item id'
        )
        name = _clean_text(raw.get('name', raw.get('productName', raw.get('product_name', ''))), 160)
        received = _number(raw.get('receivedQty', raw.get('received_qty', raw.get('quantity'))), Decimal('0'))
        expected = _number(raw.get('expectedQty', raw.get('expected_qty')), Decimal('0'))
        price_value = raw.get('unitPrice', raw.get('unit_price', raw.get('price')))
        price = None if price_value in (None, '') else _number(price_value)
        if price is not None and price < 0:
            raise ValueError('采购单价不能为负数')
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
        if require_valid and product_id is None:
            raise ValueError('审核明细必须关联有效物料')
        if product_id is not None and not _product_exists(conn, product_type, product_id):
            raise ValueError(f'物料 ID {product_id} 不存在')
        if require_valid and received <= 0:
            raise ValueError('实收数量必须大于 0')
        batch_no = _clean_text(raw.get('batchNo', raw.get('batch_no', '')), 80)
        if require_valid and not batch_no:
            raise ValueError('批次号不能为空')

        warehouse_value = raw.get('warehouseId', raw.get('warehouse_id'))
        warehouse_id = _required_int(
            default_warehouse_id if warehouse_value in (None, '') else warehouse_value,
            '明细仓库',
        )
        if not conn.execute('SELECT 1 FROM warehouses WHERE id = ?', (warehouse_id,)).fetchone():
            raise ValueError('明细仓库不存在')

        normalized.append({
            'id': _optional_int(raw.get('id'), '入库明细ID'),
            'product_type': product_type,
            'purchase_order_item_id': purchase_order_item_id,
            'product_id': product_id,
            'warehouse_id': warehouse_id,
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
            'supplier_id': _optional_int(raw.get('supplierId', raw.get('supplier_id')), '明细供应商'),
        })
    if require_valid and not normalized:
        raise ValueError('审核至少需要 1 条有效物料明细')
    return normalized


def _document_values(conn, data, existing=None, for_post=False):
    existing = existing or {}
    receipt_type = _type(data.get('type', data.get('receiptType', existing.get('receipt_type'))))
    status = _status(data.get('status', existing.get('status', 'draft')))
    if for_post:
        status = 'reviewed'
    require_valid = for_post or _is_audited(status)
    document_date = _clean_text(data.get('documentDate', data.get('document_date', existing.get('document_date', ''))), 20)
    if not document_date:
        raise ValueError('请选择单据日期')
    warehouse_id = _required_int(data.get('warehouseId', data.get('warehouse_id', existing.get('warehouse_id'))), '目标仓库')
    store_id = _optional_int(data.get('storeId', data.get('store_id', existing.get('store_id'))), '门店ID')
    supplier_id = _optional_int(data.get('supplierId', data.get('supplier_id', existing.get('supplier_id'))), '供应商ID')
    purchase_order_id = _optional_int(
        data.get('purchaseOrderId', data.get('purchase_order_id', existing.get('purchase_order_id'))),
        '采购订单ID',
    )
    source_value = data.get(
        'documentSource',
        data.get('document_source', existing.get('document_source')),
    )
    if purchase_order_id is not None:
        document_source = 'purchase-order'
    elif source_value in (None, ''):
        document_source = existing.get('document_source') or (
            'other' if receipt_type == 'raw-material' else 'production'
        )
    else:
        document_source = _clean_text(source_value, 40).lower()
        if document_source not in ('other', 'production'):
            raise ValueError('独立入库的单据来源无效')
    if purchase_order_id is None and supplier_id is not None:
        raise ValueError('有供应商的原材料请通过采购订单入库')
    settlement_type = _clean_text(data.get('settlementType', data.get('settlement_type', existing.get('settlement_type', 'none'))))
    if settlement_type not in ('none', 'pending_supplier'):
        raise ValueError('结算归属只能为无需结算或待补供应商')
    if purchase_order_id or document_source == 'production':
        settlement_type = 'none'
    workshop = _clean_text(data.get('workshop', data.get('productionWorkshop', existing.get('workshop', ''))), 80)
    if receipt_type == 'raw-material' and require_valid:
        if supplier_id is not None and not conn.execute("SELECT 1 FROM suppliers WHERE id = ? AND status = 'active'", (supplier_id,)).fetchone():
            raise ValueError('供应商不存在或已停用')
    warehouse = conn.execute('SELECT store_id FROM warehouses WHERE id = ?', (warehouse_id,)).fetchone()
    if not warehouse:
        raise ValueError('目标仓库不存在')
    if warehouse['store_id'] != store_id:
        raise ValueError('目标仓库必须属于单据门店')
    check_scope(store_id, [warehouse_id])
    items = _normalize_items(
        conn,
        receipt_type,
        data.get('items', existing.get('_items', [])),
        require_valid,
        default_warehouse_id=warehouse_id,
        allow_mixed_types=purchase_order_id is not None,
    )
    if purchase_order_id is not None:
        order_store = conn.execute('SELECT store_id FROM purchase_orders WHERE id = ?', (purchase_order_id,)).fetchone()
        if order_store and order_store['store_id'] != store_id:
            raise ValueError('入库门店必须与采购订单一致')
        _validate_purchase_link(conn, purchase_order_id, supplier_id, items, receipt_type, require_valid=require_valid)
    else:
        if any(item.get('supplier_id') for item in items):
            raise ValueError('独立入库不能填写明细供应商，请使用财务补录流程')
        for item in items:
            item['supplier_assignment_status'] = 'pending' if settlement_type == 'pending_supplier' else 'not_required'
    for item in items:
        warehouse = conn.execute('SELECT store_id FROM warehouses WHERE id = ?', (item['warehouse_id'],)).fetchone()
        if not warehouse or warehouse['store_id'] != store_id:
            raise ValueError('明细仓库必须属于单据门店')
    check_scope(store_id, [item['warehouse_id'] for item in items])
    if require_valid and not any(item['received_qty'] > 0 for item in items):
        raise ValueError('审核至少需要 1 条有效物料明细')
    total_quantity = sum(Decimal(str(item['received_qty'])) for item in items)
    total_tax = sum(
        (Decimal(str(item['tax_amount'])) for item in items),
        Decimal('0'),
    ).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    total_amount = sum(
        (Decimal(str(item['total_amount'])) for item in items),
        Decimal('0'),
    ).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    return {
        'document_no': _clean_text(data.get('documentNo', data.get('document_no', existing.get('document_no', ''))), 80),
        'document_date': document_date,
        'receipt_type': receipt_type,
        'store_id': store_id,
        'warehouse_id': warehouse_id,
        'supplier_id': supplier_id if receipt_type == 'raw-material' else None,
        'purchase_order_id': purchase_order_id,
        'document_source': document_source,
        'settlement_type': settlement_type,
        'settlement_remark': _clean_text(data.get('settlementRemark', data.get('settlement_remark', existing.get('settlement_remark', ''))), 500),
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


def _validate_purchase_link(conn, purchase_order_id, supplier_id, items, receipt_type, require_valid=False):
    """Validate the purchase association without limiting the actual received quantity."""
    order = conn.execute(
        'SELECT * FROM purchase_orders WHERE id = ?', (purchase_order_id,)
    ).fetchone()
    if not order:
        raise ValueError('关联的采购订单不存在')
    if order['status'] not in ('approved', 'partial', 'completed'):
        raise ValueError('只有已审核或部分入库的采购订单可以入库')
    check_scope(order['store_id'])
    if supplier_id is not None and order['supplier_id'] is not None and order['supplier_id'] != supplier_id:
        raise ValueError('入库供应商必须与采购订单一致')
    order_items = {
        int(row['id']): row
        for row in conn.execute(
            'SELECT * FROM purchase_order_items WHERE order_id = ?', (purchase_order_id,)
        ).fetchall()
    }
    linked = 0
    for item in items:
        link_id = item.get('purchase_order_item_id')
        if link_id is None:
            if require_valid:
                raise ValueError('采购入库明细必须关联采购订单明细')
            continue
        linked += 1
        order_item = order_items.get(int(link_id))
        if not order_item:
            raise ValueError('关联的采购订单明细不存在')
        item['supplier_id'] = order_item['supplier_id']
        item['supplier_assignment_status'] = 'confirmed'
        if order_item['product_type'] != item['product_type']:
            raise ValueError('入库类型与采购订单明细类型不一致')
        if item.get('product_id') is not None and order_item['product_id'] != item['product_id']:
            raise ValueError('入库物料与采购订单明细不一致')
        for item_field, order_field in (
            ('product_code', 'product_code'),
            ('product_name', 'product_name'),
            ('specification', 'specification'),
            ('unit', 'unit'),
        ):
            if not item.get(item_field) and order_item[order_field]:
                item[item_field] = order_item[order_field]
        remaining = float(order_item['actual_purchase_qty']) - float(order_item['received_qty'] or 0)
        if item.get('expected_qty') is None:
            item['expected_qty'] = max(remaining, 0)
        if item.get('unit_price') is None and order_item['unit_price'] is not None:
            item['unit_price'] = order_item['unit_price']
        # The inbound line may omit price because the purchase order already
        # carries it. Recalculate the derived tax and total fields after that
        # fallback so stock movement and document totals stay consistent.
        received = Decimal(str(item.get('received_qty') or 0))
        unit_price = Decimal(str(item.get('unit_price') or 0))
        tax_rate = Decimal(str(item.get('tax_rate') or 0))
        tax_amount = (received * unit_price * tax_rate / Decimal('100')).quantize(
            _MONEY_QUANT, rounding=ROUND_HALF_UP
        )
        item['tax_amount'] = float(tax_amount)
        item['total_amount'] = float(
            (received * unit_price + tax_amount).quantize(
                _MONEY_QUANT, rounding=ROUND_HALF_UP
            )
        )
    if require_valid and linked == 0:
        raise ValueError('采购入库必须关联采购订单明细')


def _serialize_item(row, default_warehouse_id=None, default_product_type=None):
    item = dict(row)
    item['productType'] = item.pop('product_type', None) or default_product_type
    item['purchaseOrderItemId'] = item.pop('purchase_order_item_id', None)
    item['productId'] = item.pop('product_id', None)
    item['warehouseId'] = item.pop('warehouse_id', None) or default_warehouse_id
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
    item['supplierId'] = item.pop('supplier_id', None)
    item['supplierAssignmentStatus'] = item.pop('supplier_assignment_status', 'not_required')
    item['supplierAssignedBy'] = item.pop('supplier_assigned_by', None)
    item['supplierAssignedAt'] = item.pop('supplier_assigned_at', None)
    item['payableTransactionId'] = item.pop('payable_transaction_id', None)
    return item


def _serialize_document(conn, row, include_items=True):
    document = dict(row)
    supplier = conn.execute(
        'SELECT supplier_name FROM suppliers WHERE id = ?',
        (row['supplier_id'],),
    ).fetchone() if row['supplier_id'] is not None else None
    warehouse = conn.execute(
        'SELECT name FROM warehouses WHERE id = ?',
        (row['warehouse_id'],),
    ).fetchone() if row['warehouse_id'] is not None else None
    store = conn.execute(
        'SELECT name FROM stores WHERE id = ?',
        (row['store_id'],),
    ).fetchone() if row['store_id'] is not None else None
    document['documentNo'] = document.pop('document_no', '')
    document['documentDate'] = document.pop('document_date', '')
    document['type'] = document.pop('receipt_type', '')
    document['storeId'] = document.pop('store_id', None)
    document['warehouseId'] = document.pop('warehouse_id', None)
    document['supplierId'] = document.pop('supplier_id', None)
    document['purchaseOrderId'] = document.pop('purchase_order_id', None)
    document['documentSource'] = document.pop('document_source', 'other')
    document['settlementType'] = document.pop('settlement_type', 'none')
    document['settlementRemark'] = document.pop('settlement_remark', '')
    document['procurementAuditedBy'] = document.pop('procurement_audited_by', None)
    document['procurementAuditedAt'] = document.pop('procurement_audited_at', None)
    document['auditedBy'] = document.pop('audited_by', '')
    document['reversedAt'] = document.pop('reversed_at', None)
    document.update(source_summary(conn, 'source_id', row['id']))
    document['supplierName'] = supplier['supplier_name'] if supplier else ''
    document['warehouseName'] = warehouse['name'] if warehouse else ''
    document['storeName'] = store['name'] if store else ''
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
        document['items'] = [
            _serialize_item(item, document['warehouseId'], document['type'])
            for item in items
        ]
        linked_suppliers = {
            item['id']: item
            for item in conn.execute(
                '''
                SELECT inbound_item.id, order_item.supplier_id, supplier.supplier_name
                FROM stock_inbound_items AS inbound_item
                JOIN purchase_order_items AS order_item
                  ON order_item.id = inbound_item.purchase_order_item_id
                LEFT JOIN suppliers AS supplier ON supplier.id = order_item.supplier_id
                WHERE inbound_item.inbound_id = ?
                ''',
                (row['id'],),
            ).fetchall()
        } if document['purchaseOrderId'] else {}
        for item in document['items']:
            linked_supplier = linked_suppliers.get(item['id'])
            if item['supplierId'] is None and linked_supplier:
                item['supplierId'] = linked_supplier['supplier_id']
            supplier_row = conn.execute(
                'SELECT supplier_name FROM suppliers WHERE id = ?', (item['supplierId'],)
            ).fetchone()
            item['supplierName'] = supplier_row['supplier_name'] if supplier_row else ''
        if not document['supplierName']:
            document['supplierName'] = '、'.join(dict.fromkeys(
                item['supplierName'] for item in document['items'] if item['supplierName']
            ))
    document['financialStatus'] = (
        'payable_confirmed' if document['payableCount'] else
        'pending_inbound' if document['purchaseOrderId'] else
        'supplier_assigned' if document['settlementType'] == 'pending_supplier' and
            document.get('items') and all(item['supplierId'] and item['unitPrice'] is not None for item in document['items']) else
        'pending_supplier' if document['settlementType'] == 'pending_supplier' else 'not_required'
    )
    return document


def _post_saved_inbound(conn, row, values):
    """Post a saved draft in the caller's transaction, without a second request."""
    inbound_id = row['id']
    if row['status'] != 'draft':
        raise FinanceError('只有待审核单据可以审核', 409)
    if conn.execute(
        "SELECT 1 FROM stock_movements WHERE movement_type = 'in' AND source_document_id = ? LIMIT 1",
        (inbound_id,),
    ).fetchone():
        raise FinanceError('该单据已有库存流水，请先检查数据状态', 409)
    checked = _document_values(conn, values, existing=values, for_post=True)
    for item in checked['items']:
        conn.execute(
            """UPDATE stock_inbound_items SET supplier_id = ?, supplier_assignment_status = ?,
               unit_price = ?, tax_amount = ?, total_amount = ? WHERE id = ? AND inbound_id = ?""",
            (item['supplier_id'], item['supplier_assignment_status'], item['unit_price'],
             item['tax_amount'], item['total_amount'], item['id'], inbound_id),
        )
    items = [dict(item) for item in conn.execute(
        'SELECT * FROM stock_inbound_items WHERE inbound_id = ? ORDER BY line_no, id', (inbound_id,),
    ).fetchall()]
    now = _now()
    conn.execute(
        """UPDATE stock_inbounds SET status = 'reviewed', posted_at = ?, updated_at = ?,
           audited_by = ?, version = version + 1, total_tax = ?, total_amount = ? WHERE id = ?""",
        (now, now, current_identity(), checked['total_tax'], checked['total_amount'], inbound_id),
    )
    audited = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
    _post_items(conn, audited, items)
    if audited['purchase_order_id']:
        post_inbound_payables(conn, audited, items)
    _update_purchase_receipts(conn, audited['purchase_order_id'], items, direction=1)
    complete_audit_notifications(conn, 'stock_inbound', inbound_id)
    return audited


def _post_on_save_requested(data):
    value = data.get('postOnSave', False)
    if not isinstance(value, bool):
        raise ValueError('postOnSave 必须为布尔值')
    if value and not admin_permission_granted(ADMIN_AUDIT_NOTIFICATION_PERMISSIONS['stock_inbound']):
        raise FinanceError('保存并入库需要入库审核权限', 403)
    return value


def _post_items(conn, document_row, item_rows):
    """Apply an audited document in the caller's transaction."""
    default_type = document_row['receipt_type']
    now = _now()
    for item in item_rows:
        receipt_type = item.get('product_type') or default_type
        qty = float(item['received_qty'] or 0)
        if qty <= 0 or item['product_id'] is None:
            continue
        product_id = int(item['product_id'])
        warehouse_id = int(item.get('warehouse_id') or document_row['warehouse_id'] or 0)
        store_id = int(document_row['store_id'] or 0)
        bin_code = item['bin_code'] or ''
        batch_no = item['batch_no'] or ''
        expense_cost = conn.execute(
            """SELECT COALESCE(SUM(amount_excluding_tax_cents), 0) AS amount
               FROM purchase_expense_lines WHERE inbound_item_id = ?
               AND status = 'confirmed' AND include_in_inventory_cost = 1""", (item['id'],),
        ).fetchone()['amount'] / 100
        inventory_price = float(item['unit_price'] or 0) + expense_cost / qty
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
                qty, inventory_price, item['tax_rate'], float(item['total_amount']) + expense_cost, now,
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


def _reverse_posted_items(conn, document_row):
    """Reverse inventory movements written by one inbound document."""
    movements = conn.execute(
        '''
        SELECT * FROM stock_movements
        WHERE movement_type = 'in' AND source_document_id = ?
        ORDER BY id
        ''',
        (document_row['id'],),
    ).fetchall()
    for movement in movements:
        quantity = float(movement['quantity'] or 0)
        balance = conn.execute(
            '''
            SELECT quantity FROM stock_balances
            WHERE product_type = ? AND product_id = ? AND warehouse_id = ?
              AND store_id = ? AND bin_code = ? AND batch_no = ?
            ''',
            (
                movement['product_type'], movement['product_id'], movement['warehouse_id'],
                movement['store_id'], movement['bin_code'], movement['batch_no'],
            ),
        ).fetchone()
        if not balance or float(balance['quantity'] or 0) + 0.0000001 < quantity:
            raise ValueError('当前库存不足，无法反审核该入库单')
        conn.execute(
            '''
            UPDATE stock_balances
            SET quantity = quantity - ?, updated_at = ?
            WHERE product_type = ? AND product_id = ? AND warehouse_id = ?
              AND store_id = ? AND bin_code = ? AND batch_no = ?
            ''',
            (
                quantity, _now(), movement['product_type'], movement['product_id'],
                movement['warehouse_id'], movement['store_id'], movement['bin_code'],
                movement['batch_no'],
            ),
        )
        if movement['product_type'] == 'finished-product':
            conn.execute(
                '''
                UPDATE inventory
                SET stock = COALESCE(stock, 0) - ?, updated_at = ?
                WHERE product_id = ?
                ''',
                (quantity, _now(), movement['product_id']),
            )
    conn.execute(
        "DELETE FROM stock_movements WHERE movement_type = 'in' AND source_document_id = ?",
        (document_row['id'],),
    )
    conn.execute('DELETE FROM stock_balances WHERE ABS(quantity) < 0.0000001')


def _update_purchase_receipts(conn, purchase_order_id, item_rows, direction=1):
    if not purchase_order_id:
        return
    for item in item_rows:
        link_id = item.get('purchase_order_item_id')
        if link_id is None:
            continue
        quantity = float(item.get('received_qty') or 0) * direction
        if abs(quantity) < 0.0000001:
            continue
        conn.execute(
            'UPDATE purchase_order_items SET received_qty = received_qty + ? WHERE id = ? AND order_id = ?',
            (quantity, link_id, purchase_order_id),
        )
    remaining = conn.execute(
        '''
        SELECT COALESCE(SUM(CASE WHEN actual_purchase_qty > received_qty
                                THEN actual_purchase_qty - received_qty ELSE 0 END), 0) AS quantity
        FROM purchase_order_items WHERE order_id = ?
        ''',
        (purchase_order_id,),
    ).fetchone()['quantity']
    received = conn.execute(
        'SELECT COALESCE(SUM(received_qty), 0) AS quantity FROM purchase_order_items WHERE order_id = ?',
        (purchase_order_id,),
    ).fetchone()['quantity']
    new_status = 'completed' if float(remaining or 0) <= 0.0000001 else 'partial' if float(received or 0) > 0.0000001 else 'approved'
    conn.execute(
        'UPDATE purchase_orders SET status = ?, updated_at = ?, version = version + 1 WHERE id = ? AND status <> \'cancelled\'',
        (new_status, _now(), purchase_order_id),
    )


def _insert_items(conn, inbound_id, receipt_type, items):
    for line_no, item in enumerate(items, start=1):
        cursor = conn.execute(
            '''
            INSERT INTO stock_inbound_items (
                inbound_id, line_no, product_type, product_id, purchase_order_item_id, warehouse_id, product_code,
                product_name, specification, unit, expected_qty, received_qty,
                bin_code, batch_no, unit_price, tax_rate, tax_amount,
                total_amount, remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                inbound_id, line_no, item.get('product_type') or receipt_type, item['product_id'], item.get('purchase_order_item_id'), item['warehouse_id'], item['product_code'],
                item['product_name'], item['specification'], item['unit'], item['expected_qty'],
                item['received_qty'], item['bin_code'], item['batch_no'], item['unit_price'],
                item['tax_rate'], item['tax_amount'], item['total_amount'], item['remark'],
            ),
        )
        item['id'] = cursor.lastrowid
        conn.execute(
            "UPDATE stock_inbound_items SET supplier_id = ?, supplier_assignment_status = ? WHERE id = ?",
            (item.get('supplier_id'), item.get('supplier_assignment_status', 'not_required'), item['id']),
        )


def _document_insert(conn, values):
    now = _now()
    purchase_order_id = values.get('purchase_order_id')
    if purchase_order_id:
        order = conn.execute('SELECT status, store_id FROM purchase_orders WHERE id = ?', (purchase_order_id,)).fetchone()
        if order['status'] == 'completed':
            raise FinanceError('采购订单已完成入库，请新建采购订单或独立入库', 409)
        if order['store_id'] != values['store_id']:
            raise ValueError('入库门店必须与采购订单一致')
        for item in values['items']:
            order_item = conn.execute(
                'SELECT actual_purchase_qty, received_qty FROM purchase_order_items WHERE id = ?',
                (item['purchase_order_item_id'],),
            ).fetchone()
            if order_item and order_item['received_qty'] >= order_item['actual_purchase_qty']:
                raise FinanceError('已完成的采购明细不能补充入库', 409)
        previous = conn.execute(
            'SELECT document_no FROM stock_inbounds WHERE purchase_order_id = ? ORDER BY id LIMIT 1',
            (purchase_order_id,),
        ).fetchone()
        if previous:
            values['document_no'] = previous['document_no']
        draft = conn.execute(
            "SELECT 1 FROM stock_inbounds WHERE purchase_order_id = ? AND status = 'draft'",
            (purchase_order_id,),
        ).fetchone()
        if draft:
            raise ValueError('该采购订单已有待审核入库批次，请先处理')
    _validate_document_number(conn, values['document_no'], purchase_order_id)
    cursor = conn.execute(
        '''
        INSERT INTO stock_inbounds (
            document_no, document_date, receipt_type, store_id, warehouse_id,
            supplier_id, purchase_order_id, document_source, workshop, inspector, quality_no, remark, attachments,
            status, total_quantity, total_tax, total_amount, posted_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            values['document_no'] or f'TEMP-{now.replace(" ", "").replace(":", "").replace("-", "")}-{threading.get_ident()}',
            values['document_date'], values['receipt_type'], values['store_id'], values['warehouse_id'],
            values['supplier_id'], values.get('purchase_order_id'), values['document_source'], values['workshop'], values['inspector'], values['quality_no'],
            values['remark'], json.dumps(values['attachments'], ensure_ascii=False), values['status'],
            values['total_quantity'], values['total_tax'], values['total_amount'],
            now if _is_audited(values['status']) else None, now, now,
        ),
    )
    inbound_id = cursor.lastrowid
    conn.execute(
        "UPDATE stock_inbounds SET settlement_type = ?, settlement_remark = ? WHERE id = ?",
        (values['settlement_type'], values['settlement_remark'], inbound_id),
    )
    if not values['document_no']:
        generated = f"RK{values['document_date'].replace('-', '')[:8]}{inbound_id:03d}"
        _validate_document_number(conn, generated, purchase_order_id, inbound_id)
        conn.execute('UPDATE stock_inbounds SET document_no = ? WHERE id = ?', (generated, inbound_id))
    row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
    _insert_items(conn, inbound_id, values['receipt_type'], values['items'])
    if purchase_order_id:
        conn.execute(
            'UPDATE purchase_orders SET inbound_deleted_at = NULL WHERE id = ?',
            (purchase_order_id,),
        )
    if _is_audited(values['status']):
        _post_items(conn, row, [dict(item, id=item.get('id')) for item in values['items']])
    return conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()


def _validate_document_number(conn, document_no, purchase_order_id, exclude_id=0):
    if not document_no:
        return
    duplicate = conn.execute(
        'SELECT 1 FROM stock_inbounds WHERE document_no = ? AND id <> ? '
        'AND (? IS NULL OR purchase_order_id IS NOT ?) LIMIT 1',
        (document_no, exclude_id, purchase_order_id, purchase_order_id),
    ).fetchone()
    if duplicate:
        raise ValueError('入库单号已被其他单据使用')


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
    business_type = _clean_text(request.args.get('businessType')).lower()
    settlement_type = request.args.get('settlementType')
    if business_type not in ('', 'purchase', 'production'):
        return jsonify({'success': False, 'message': '入库业务类型无效'}), 400
    with get_db() as conn:
        sql = 'SELECT * FROM stock_inbounds WHERE 1 = 1'
        params = []
        from utils.supplier_ledger import scope_sql
        scoped, scoped_params = scope_sql(alias='stock_inbounds')
        sql += scoped
        params.extend(scoped_params)
        if settlement_type:
            if settlement_type not in ('none', 'pending_supplier'):
                return jsonify({'success': False, 'message': '结算归属无效'}), 400
            sql += ' AND settlement_type = ? AND purchase_order_id IS NULL'
            params.append(settlement_type)
        if business_type == 'purchase':
            sql += " AND document_source IN ('other', 'purchase-order')"
        elif business_type == 'production':
            sql += " AND receipt_type = 'finished-product' AND document_source = 'production'"
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
        try:
            check_scope(row['store_id'])
        except FinanceError as exc:
            return jsonify({'success': False, 'message': str(exc)}), exc.status
        return jsonify(_serialize_document(conn, row))


@stock_inbounds_bp.route('/stock-inbounds', methods=['POST'])
def create_stock_inbound():
    data = request.get_json(silent=True) or {}
    requested_status = str(data.get('status') or 'draft').lower()
    try:
        post_on_save = _post_on_save_requested(data)
        if _is_audited(requested_status):
            return jsonify({'success': False, 'message': '请先保存待审核单据，再调用审核接口'}), 400
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                values = _document_values(conn, data)
                if post_on_save:
                    if values['purchase_order_id'] or values['document_source'] != 'other':
                        raise ValueError('保存并入库仅用于独立进货单')
                    values['settlement_type'] = 'pending_supplier'
                should_post = post_on_save or bool(values['purchase_order_id'])
                replay, token = idempotent_result(conn, 'inbound:create', data)
                if replay:
                    check_scope(replay['stockIn']['storeId'], [
                        item['warehouseId'] for item in replay['stockIn']['items']
                    ])
                    return jsonify(replay)
                row = _document_insert(conn, values)
                if should_post:
                    row, saved_values = _existing_values(conn, row['id'])
                    row = _post_saved_inbound(conn, row, saved_values)
                else:
                    create_audit_notifications(
                        conn,
                        "stock_inbound",
                        row["id"],
                        row["document_no"],
                        f"入库单 {row['document_no']} 已提交，请及时审核。",
                    )
                return jsonify(save_operation(conn, token, {
                    'success': True,
                    'message': '进货单保存成功，实收数量已入库' if should_post else '入库单保存成功',
                    'stockIn': _serialize_document(conn, row), 'id': row['id'],
                })), 201
    except FinanceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '入库单保存失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>', methods=['PUT'])
def update_stock_inbound(inbound_id):
    data = request.get_json(silent=True) or {}
    requested_status = str(data.get('status') or '').lower()
    try:
        post_on_save = _post_on_save_requested(data)
        if _is_audited(requested_status):
            return jsonify({'success': False, 'message': '请通过审核接口变更审核状态'}), 400
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                old_row, old_values = _existing_values(conn, inbound_id)
                if not old_row:
                    return jsonify({'success': False, 'message': '入库单不存在'}), 404
                check_scope(old_row['store_id'], [item['warehouse_id'] for item in old_values['_items']])
                replay, token = idempotent_result(conn, f'inbound:{inbound_id}:update', data)
                if replay:
                    return jsonify(replay)
                if _is_audited(old_row['status']):
                    return jsonify({'success': False, 'message': '已审核单据不可修改'}), 409
                check_scope(old_row['store_id'])
                check_version(data, old_row)
                if conn.execute('SELECT 1 FROM purchase_expense_lines WHERE inbound_item_id IN '
                                '(SELECT id FROM stock_inbound_items WHERE inbound_id = ?)', (inbound_id,)).fetchone():
                    raise FinanceError('请先删除或取消该批次的费用归属，再修改入库明细', 409)
                values = _document_values(conn, data, existing=old_values)
                if post_on_save:
                    if old_row['status'] != 'draft' or values['purchase_order_id'] or values['document_source'] != 'other':
                        raise ValueError('保存并入库仅用于独立进货草稿')
                    values['settlement_type'] = 'pending_supplier'
                should_post = post_on_save or bool(values.get('purchase_order_id'))
                if values.get('purchase_order_id') != old_row['purchase_order_id']:
                    raise ValueError('不能修改入库批次关联的采购订单')
                now = _now()
                document_no = old_row['document_no'] if old_row['purchase_order_id'] else values['document_no'] or old_row['document_no']
                _validate_document_number(conn, document_no, values.get('purchase_order_id'), inbound_id)
                conn.execute(
                    '''
                    UPDATE stock_inbounds SET document_no = ?, document_date = ?, receipt_type = ?,
                        store_id = ?, warehouse_id = ?, supplier_id = ?, purchase_order_id = ?, document_source = ?, workshop = ?, inspector = ?,
                        quality_no = ?, remark = ?, attachments = ?, status = ?, total_quantity = ?,
                        total_tax = ?, total_amount = ?, posted_at = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        document_no, values['document_date'], values['receipt_type'], values['store_id'],
                        values['warehouse_id'], values['supplier_id'], values.get('purchase_order_id'), values['document_source'], values['workshop'], values['inspector'],
                        values['quality_no'], values['remark'], json.dumps(values['attachments'], ensure_ascii=False),
                        values['status'], values['total_quantity'], values['total_tax'], values['total_amount'],
                        now if _is_audited(values['status']) else None, now, inbound_id,
                    ),
                )
                conn.execute('DELETE FROM stock_inbound_items WHERE inbound_id = ?', (inbound_id,))
                conn.execute(
                    "UPDATE stock_inbounds SET settlement_type = ?, settlement_remark = ?, version = version + 1 WHERE id = ?",
                    (values['settlement_type'], values['settlement_remark'], inbound_id),
                )
                _insert_items(conn, inbound_id, values['receipt_type'], values['items'])
                if _is_audited(values['status']):
                    new_row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                    _post_items(conn, new_row, [dict(item, id=item.get('id')) for item in values['items']])
                row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                if should_post:
                    row, saved_values = _existing_values(conn, inbound_id)
                    row = _post_saved_inbound(conn, row, saved_values)
                return jsonify(save_operation(conn, token, {
                    'success': True,
                    'message': '进货单保存成功，实收数量已入库' if should_post else '入库单更新成功',
                    'stockIn': _serialize_document(conn, row),
                }))
    except FinanceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '入库单更新失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>', methods=['DELETE'])
def cancel_stock_inbound(inbound_id):
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                if not row:
                    return jsonify({'success': False, 'message': '入库单不存在'}), 404
                check_scope(row['store_id'])
                check_version(data, row)
                if _is_audited(row['status']):
                    return jsonify({'success': False, 'message': '已审核单据不能直接删除，请先反审核'}), 409
                if conn.execute(
                    'SELECT 1 FROM purchase_expense_lines WHERE inbound_item_id IN '
                    '(SELECT id FROM stock_inbound_items WHERE inbound_id = ?) LIMIT 1',
                    (inbound_id,),
                ).fetchone():
                    raise FinanceError('请先删除或取消该批次的费用归属，再作废入库单', 409)
                if row['status'] == 'cancelled':
                    complete_audit_notifications(conn, "stock_inbound", inbound_id)
                    conn.execute('DELETE FROM stock_inbound_items WHERE inbound_id = ?', (inbound_id,))
                    conn.execute('DELETE FROM stock_inbounds WHERE id = ?', (inbound_id,))
                    return jsonify({'success': True, 'message': '已红冲入库单已删除', 'deleted': True})
                conn.execute(
                    "UPDATE stock_inbounds SET status = 'cancelled', version = version + 1, updated_at = ? WHERE id = ?",
                    (_now(), inbound_id),
                )
                complete_audit_notifications(conn, "stock_inbound", inbound_id)
                return jsonify({'success': True, 'message': '入库单已作废'})
    except FinanceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '入库单作废失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/purchase-inbounds/bulk-delete', methods=['POST'])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS['delete'])
def delete_purchase_inbounds():
    data = request.get_json(silent=True) or {}
    try:
        selections = {}
        for field in ('purchaseApplicationIds', 'purchaseOrderIds', 'inboundIds'):
            raw_ids = data.get(field, [])
            if not isinstance(raw_ids, list) or len(raw_ids) > 500:
                raise ValueError('删除 ID 必须是最多 500 项的数组')
            ids = {_required_int(value, '删除 ID') for value in raw_ids}
            if any(value <= 0 for value in ids):
                raise ValueError('删除 ID 必须为正整数')
            selections[field] = ids
        application_ids = selections['purchaseApplicationIds']
        order_ids = selections['purchaseOrderIds']
        inbound_ids = selections['inboundIds']
        if not application_ids and not order_ids and not inbound_ids:
            raise ValueError('请先勾选需要删除的入库记录')
        if application_ids.intersection(order_ids):
            raise ValueError('采购申请不能重复提交删除')
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                applications = []
                if application_ids:
                    placeholders = ','.join('?' for _ in application_ids)
                    applications = conn.execute(
                        f"SELECT * FROM purchase_orders WHERE id IN ({placeholders})",
                        tuple(application_ids),
                    ).fetchall()
                    if len(applications) != len(application_ids):
                        raise ValueError('部分采购申请不存在，请刷新列表')
                    if any(
                        row['source_type'] != 'inbound-application'
                        or row['status'] not in ('draft', 'pending')
                        for row in applications
                    ):
                        raise FinanceError('只有草稿或待审核采购申请可以删除', 409)
                    for row in applications:
                        check_scope(row['store_id'])
                    for order_id in application_ids:
                        if conn.execute(
                            'SELECT 1 FROM stock_inbounds WHERE purchase_order_id = ? '
                            'UNION ALL SELECT 1 FROM purchase_expense_lines WHERE purchase_order_id = ? LIMIT 1',
                            (order_id, order_id),
                        ).fetchone():
                            raise FinanceError('采购申请已关联入库或费用，不能删除', 409)
                orders = []
                if order_ids:
                    placeholders = ','.join('?' for _ in order_ids)
                    orders = conn.execute(
                        f'SELECT * FROM purchase_orders WHERE id IN ({placeholders})',
                        tuple(order_ids),
                    ).fetchall()
                    if len(orders) != len(order_ids):
                        raise ValueError('部分采购订单不存在，请刷新列表')
                    if any(order['status'] in ('confirmed', 'approved', 'partial', 'completed') for order in orders):
                        raise FinanceError('采购审核通过的采购订单入库不能删除', 409)
                    for order in orders:
                        check_scope(order['store_id'])
                    inbound_ids.update(row['id'] for row in conn.execute(
                        f'SELECT id FROM stock_inbounds WHERE purchase_order_id IN ({placeholders})',
                        tuple(order_ids),
                    ).fetchall())
                rows = []
                if inbound_ids:
                    placeholders = ','.join('?' for _ in inbound_ids)
                    rows = conn.execute(
                        f'SELECT * FROM stock_inbounds WHERE id IN ({placeholders}) ORDER BY id DESC',
                        tuple(inbound_ids),
                    ).fetchall()
                    if len(rows) != len(inbound_ids):
                        raise ValueError('部分入库记录不存在，请刷新列表')
                    if any(row['document_source'] == 'production' for row in rows):
                        raise ValueError('不能通过采购页面删除生产入库记录')
                    if any(row['procurement_audited_at'] for row in rows):
                        raise FinanceError('采购审核通过的入库单不能删除', 409)
                    if any(row['purchase_order_id'] and row['purchase_order_id'] not in order_ids for row in rows):
                        raise ValueError('关联采购订单的入库记录必须按采购单整组删除')
                    if any(_is_audited(row['status']) for row in rows) and not admin_permission_granted(ADMIN_AUDIT_NOTIFICATION_PERMISSIONS['stock_inbound']):
                        return jsonify({'success': False, 'message': '删除已审核入库需要入库审核权限'}), 403
                for row in rows:
                    check_scope(row['store_id'])
                    if _is_audited(row['status']):
                        items = [dict(item) for item in conn.execute(
                            'SELECT * FROM stock_inbound_items WHERE inbound_id = ?', (row['id'],)
                        ).fetchall()]
                        reverse_inbound_payables(conn, row)
                        _reverse_posted_items(conn, row)
                        _update_purchase_receipts(conn, row['purchase_order_id'], items, direction=-1)
                    complete_audit_notifications(conn, 'stock_inbound', row['id'])
                    conn.execute('DELETE FROM purchase_expense_lines WHERE inbound_item_id IN '
                                 '(SELECT id FROM stock_inbound_items WHERE inbound_id = ?)', (row['id'],))
                    conn.execute('DELETE FROM stock_inbound_items WHERE inbound_id = ?', (row['id'],))
                    conn.execute('DELETE FROM stock_inbounds WHERE id = ?', (row['id'],))
                for order in applications:
                    complete_audit_notifications(conn, 'purchase_order', order['id'])
                    conn.execute('DELETE FROM purchase_order_items WHERE order_id = ?', (order['id'],))
                    conn.execute('DELETE FROM purchase_orders WHERE id = ?', (order['id'],))
                for order in orders:
                    conn.execute(
                        'UPDATE purchase_orders SET inbound_deleted_at = ?, updated_at = ? WHERE id = ?',
                        (_now(), _now(), order['id']),
                    )
                return jsonify({
                    'success': True, 'message': '所选采购入库记录已删除',
                    'deletedCount': len(rows) + len(applications),
                })
    except FinanceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 409
    except Exception as exc:
        return jsonify({'success': False, 'message': '删除失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>/restart', methods=['POST'])
def restart_stock_inbound(inbound_id):
    """将已红冲且未写库存的单据重新置为待审核。"""
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                if not row:
                    return jsonify({'success': False, 'message': '入库单不存在'}), 404
                check_scope(row['store_id'])
                check_version(data, row)
                if row['status'] != 'cancelled':
                    return jsonify({'success': False, 'message': '只有已红冲单据可以重新启用'}), 409
                now = _now()
                conn.execute(
                    "UPDATE stock_inbounds SET status = 'draft', version = version + 1, updated_at = ? WHERE id = ?",
                    (now, inbound_id),
                )
                updated = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                create_audit_notifications(
                    conn,
                    "stock_inbound",
                    inbound_id,
                    updated["document_no"],
                    f"入库单 {updated['document_no']} 已重新提交，请及时审核。",
                    event_version=f"restart:{now}",
                )
                return jsonify({
                    'success': True,
                    'message': '入库单已重新启用',
                    'stockIn': _serialize_document(conn, updated),
                })
    except FinanceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '入库单重新启用失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>/audit', methods=['POST'])
@require_admin_permission(ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["stock_inbound"])
def audit_stock_inbound(inbound_id):
    """审核待审核入库单，并在同一事务内写入库存余额和流水。"""
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                row, values = _existing_values(conn, inbound_id)
                if not row:
                    return jsonify({'success': False, 'message': '入库单不存在'}), 404
                check_scope(row['store_id'])
                data = request.get_json(silent=True) or {}
                if row['purchase_order_id']:
                    raise FinanceError('关联采购订单的入库已在保存时自动入账，无需重复审核', 409)
                replay, token = idempotent_result(conn, f'inbound:{inbound_id}:audit', data)
                if replay:
                    return jsonify(replay)
                if _is_audited(row['status']):
                    return jsonify(save_operation(conn, token, {'success': True, 'stockIn': _serialize_document(conn, row)}))
                check_version(data, row)
                audited_row = _post_saved_inbound(conn, row, values)
                return jsonify(save_operation(conn, token, {
                    'success': True,
                    'message': '入库单审核成功，库存已更新',
                    'stockIn': _serialize_document(conn, audited_row),
                }))
    except FinanceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '入库单审核失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-inbounds/<int:inbound_id>/audit', methods=['DELETE'])
@require_admin_permission(ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["stock_inbound"])
def reverse_audit_stock_inbound(inbound_id):
    """反审核入库单，并回退该单据此前写入的库存流水。"""
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                row = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                if not row:
                    return jsonify({'success': False, 'message': '入库单不存在'}), 404
                check_scope(row['store_id'])
                data = request.get_json(silent=True) or {}
                if row['purchase_order_id']:
                    raise FinanceError('关联采购订单的入库不使用库存记录反审核', 409)
                replay, token = idempotent_result(conn, f'inbound:{inbound_id}:reverse', data)
                if replay:
                    return jsonify(replay)
                if not _is_audited(row['status']):
                    if row['status'] == 'draft' and row['reversed_at']:
                        return jsonify(save_operation(conn, token, {'success': True, 'stockIn': _serialize_document(conn, row)}))
                    return jsonify({'success': False, 'message': '当前单据未审核'}), 409
                check_version(data, row)
                item_rows = conn.execute(
                    'SELECT * FROM stock_inbound_items WHERE inbound_id = ? ORDER BY line_no, id',
                    (inbound_id,),
                ).fetchall()
                reverse_inbound_payables(conn, row)
                _reverse_posted_items(conn, row)
                if not row['purchase_order_id']:
                    conn.execute(
                        """UPDATE stock_inbound_items SET supplier_id = NULL,
                           supplier_assignment_status = CASE WHEN ? = 'pending_supplier' THEN 'pending' ELSE 'not_required' END,
                           supplier_assigned_by = NULL, supplier_assigned_at = NULL WHERE inbound_id = ?""",
                        (row['settlement_type'], inbound_id),
                    )
                _update_purchase_receipts(conn, row['purchase_order_id'], [dict(item) for item in item_rows], direction=-1)
                now = _now()
                conn.execute(
                    "UPDATE stock_inbounds SET status = 'draft', posted_at = NULL, updated_at = ?, reversed_at = ?, version = version + 1 WHERE id = ?",
                    (now, now, inbound_id),
                )
                updated = conn.execute('SELECT * FROM stock_inbounds WHERE id = ?', (inbound_id,)).fetchone()
                create_audit_notifications(
                    conn,
                    "stock_inbound",
                    inbound_id,
                    updated["document_no"],
                    f"入库单 {updated['document_no']} 已反审核，请重新审核。",
                    event_version=f"reverse:{now}",
                )
                return jsonify(save_operation(conn, token, {
                    'success': True,
                    'message': '入库单已反审核，库存已回退',
                    'stockIn': _serialize_document(conn, updated),
                }))
    except FinanceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 409
    except Exception as exc:
        return jsonify({'success': False, 'message': '入库单反审核失败', 'detail': str(exc)}), 500


@stock_inbounds_bp.route('/stock-balances', methods=['GET'])
def list_stock_balances():
    receipt_type = request.args.get('type')
    with get_db() as conn:
        sql = '''
            WITH inbound_costs AS (
                SELECT product_type, product_id, warehouse_id, store_id, bin_code, batch_no,
                       SUM(
                           CASE WHEN unit_price IS NOT NULL
                                THEN quantity * unit_price
                                ELSE 0 END
                       ) AS priced_amount,
                       SUM(quantity) AS inbound_quantity
                FROM stock_movements
                WHERE movement_type = 'in'
                GROUP BY product_type, product_id, warehouse_id, store_id, bin_code, batch_no
            ),
            valued_balances AS (
                SELECT balance.product_type, balance.product_id,
                       balance.warehouse_id, balance.store_id,
                       balance.quantity, balance.updated_at,
                       COALESCE(
                           costs.priced_amount / NULLIF(costs.inbound_quantity, 0),
                           0
                       ) AS average_unit_cost
                FROM stock_balances AS balance
                LEFT JOIN inbound_costs AS costs
                  ON costs.product_type = balance.product_type
                 AND costs.product_id = balance.product_id
                 AND costs.warehouse_id = balance.warehouse_id
                 AND costs.store_id = balance.store_id
                 AND costs.bin_code = balance.bin_code
                 AND costs.batch_no = balance.batch_no
            )
            SELECT product_type, product_id, warehouse_id, store_id,
                   SUM(quantity) AS quantity,
                   CASE WHEN ABS(SUM(quantity)) > 0.0000001
                        THEN SUM(quantity * average_unit_cost) / SUM(quantity)
                        ELSE 0 END AS average_unit_cost,
                   SUM(quantity * average_unit_cost) AS inventory_amount,
                   MAX(updated_at) AS updated_at
            FROM valued_balances
            WHERE 1 = 1
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
                'averageUnitCost': round(row['average_unit_cost'] or 0, 6),
                'inventoryAmount': round(row['inventory_amount'] or 0, 2),
                'updatedAt': row['updated_at'],
            }
            for row in rows
        ])


@stock_inbounds_bp.route('/stock-movements', methods=['GET'])
def list_stock_movements():
    """Return posted inventory movements for a material/location detail view."""
    try:
        product_type = _type(request.args.get('type') or 'raw-material')
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400

    product_id = request.args.get('productId', type=int)
    warehouse_id = request.args.get('warehouseId', type=int)
    store_id = request.args.get('storeId', type=int)
    limit = request.args.get('limit', default=200, type=int)
    limit = min(max(limit or 200, 1), 500)

    if product_id is None:
        return jsonify({'success': False, 'message': '请提供原材料ID'}), 400

    with get_db() as conn:
        sql = '''
            SELECT
                movement.movement_type,
                movement.receipt_type,
                movement.source_document_id,
                movement.source_document_no,
                movement.product_type,
                movement.product_id,
                movement.warehouse_id,
                movement.store_id,
                SUM(movement.quantity) AS quantity,
                CASE
                    WHEN movement.movement_type = 'in'
                    THEN SUM(
                        movement.quantity * COALESCE(movement.unit_price, 0)
                    ) / NULLIF(SUM(movement.quantity), 0)
                    ELSE NULL
                END AS unit_price,
                CASE
                    WHEN movement.movement_type = 'in'
                    THEN SUM(COALESCE(movement.total_amount, 0))
                    ELSE NULL
                END AS total_amount,
                MAX(movement.created_at) AS created_at,
                COALESCE(
                    MAX(inbound.document_date),
                    MAX(outbound.document_date),
                    MAX(movement.created_at)
                ) AS document_date,
                MAX(store.name) AS store_name,
                MAX(warehouse.name) AS warehouse_name,
                COALESCE(MAX(outbound.remark), MAX(inbound.remark), '') AS remark,
                MAX(outbound.produced_quantity) AS produced_quantity,
                GROUP_CONCAT(
                    DISTINCT CASE
                        WHEN trim(COALESCE(movement.batch_no, '')) <> ''
                        THEN movement.batch_no
                    END
                ) AS batch_nos
            FROM stock_movements AS movement
            LEFT JOIN stores AS store ON store.id = movement.store_id
            LEFT JOIN warehouses AS warehouse ON warehouse.id = movement.warehouse_id
            LEFT JOIN stock_inbounds AS inbound
              ON movement.movement_type = 'in'
             AND inbound.id = movement.source_document_id
            LEFT JOIN material_outbounds AS outbound
              ON movement.movement_type = 'out'
             AND outbound.id = movement.source_document_id
            WHERE movement.product_type = ?
              AND movement.product_id = ?
              AND movement.movement_type IN ('in', 'out')
        '''
        params = [product_type, product_id]
        if warehouse_id is not None:
            sql += ' AND movement.warehouse_id = ?'
            params.append(warehouse_id)
        if store_id is not None:
            sql += ' AND movement.store_id = ?'
            params.append(store_id)
        sql += '''
            GROUP BY
                movement.movement_type,
                movement.receipt_type,
                movement.source_document_id,
                movement.source_document_no,
                movement.product_type,
                movement.product_id,
                movement.warehouse_id,
                movement.store_id
            ORDER BY MAX(movement.created_at) DESC, MAX(movement.id) DESC
            LIMIT ?
        '''
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return jsonify([
            {
                'movementType': row['movement_type'],
                'receiptType': row['receipt_type'],
                'sourceDocumentId': row['source_document_id'],
                'documentNo': row['source_document_no'],
                'productType': row['product_type'],
                'productId': row['product_id'],
                'warehouseId': row['warehouse_id'],
                'storeId': row['store_id'],
                'quantity': float(row['quantity'] or 0),
                'unitPrice': (
                    round(float(row['unit_price']), 6)
                    if row['unit_price'] is not None else None
                ),
                'totalAmount': (
                    round(float(row['total_amount']), 2)
                    if row['total_amount'] is not None else None
                ),
                'createdAt': row['created_at'] or '',
                'documentDate': row['document_date'] or '',
                'storeName': row['store_name'] or '',
                'warehouseName': row['warehouse_name'] or '',
                'remark': row['remark'] or '',
                'producedQuantity': (
                    float(row['produced_quantity'])
                    if row['produced_quantity'] is not None else None
                ),
                'batchNos': row['batch_nos'] or '',
            }
            for row in rows
        ])
