export const DOCUMENT_TYPES = Object.freeze({
  sale: { title: '销售订单', partyLabel: '客户', partyField: 'customerId', dateField: 'orderDate', numberField: 'orderNumber', remarkField: 'orderRemark', specField: 'spec', includedField: 'totalAmount', printType: 'sale', showPackages: true },
  'sale-return': { title: '销售退货单', partyLabel: '客户', partyField: 'customerId', dateField: 'returnDate', numberField: 'returnNumber', remarkField: 'remark', specField: 'specification', includedField: 'taxIncludedAmount', printType: 'return', showPackages: true },
  purchase: { title: '进货单', partyLabel: '供应商', partyField: 'supplierId', dateField: 'documentDate', numberField: 'documentNo', remarkField: 'remark', specField: 'specification', includedField: 'taxIncludedAmount', printType: 'purchase', showPackages: false },
  'purchase-order': { title: '采购申请', dateLabel: '申请日期', dateField: 'orderDate', numberField: 'orderNo', remarkField: 'remark', specField: 'specification', showPackages: false }
})

export const DOCUMENT_ACTIONS = ['create', 'edit', 'copy', 'view', 'audit']
export const localDate = () => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}
export const money = value => Number(value || 0).toFixed(2)
export const isLockedInbound = status => ['reviewed', 'posted', 'cancelled', 'red-flushed'].includes(status)

// Keep inbound wire fields separate from sales/return fields, even where labels match.
export function purchasePayload(form) {
  return {
    documentNo: form.documentNo,
    documentDate: form.documentDate,
    type: 'raw-material',
    storeId: Number(form.storeId),
    supplierId: form.supplierId ? Number(form.supplierId) : null,
    purchaseOrderId: form.purchaseOrderId ? Number(form.purchaseOrderId) : null,
    warehouseId: Number(form.warehouseId),
    inspector: form.inspector,
    qualityNo: form.qualityNo,
    remark: form.remark,
    attachments: form.attachments || [],
    status: 'draft',
    items: form.items.filter(item => item.productId).map(item => ({
      productId: Number(item.productId),
      purchaseOrderItemId: item.purchaseOrderItemId ? Number(item.purchaseOrderItemId) : null,
      warehouseId: Number(item.warehouseId || form.warehouseId),
      code: item.productCode,
      name: item.goodsName,
      specification: item.specification,
      unit: item.unit,
      expectedQty: item.expectedQty === '' || item.expectedQty == null ? null : Number(item.expectedQty),
      receivedQty: Number(item.quantity),
      unitPrice: item.price === '' || item.price == null ? null : Number(item.price),
      taxRate: form.taxEnabled ? Number(item.taxRate) || 0 : 0,
      batchNo: item.batchNo,
      binCode: item.binCode,
      remark: item.remark
    }))
  }
}

export function validatePurchase(form, onInvalid = () => {}) {
  const invalid = (key, message) => { onInvalid(key, message); return message }
  if (!form.storeId) return invalid('storeId', '请选择门店。')
  if (!form.supplierId && !form.purchaseOrderId) return invalid('supplierId', '请选择供应商。')
  if (!form.warehouseId) return invalid('warehouseId', '请选择仓库。')
  if (!form.documentDate) return invalid('documentDate', '请选择单据日期。')
  const items = form.items.filter(item => item.productId)
  if (!items.length) return invalid('item-product-0', '请至少选择一条物料。')
  for (const [index, item] of form.items.entries()) {
    if (!item.productId) continue
    if (!Number.isFinite(Number(item.quantity)) || Number(item.quantity) <= 0) return invalid(`item-quantity-${index}`, '实收数量必须大于 0。')
    if (!item.batchNo?.trim()) return invalid(`item-batch-${index}`, '请填写物料的批次号。')
    if (!Number.isFinite(Number(item.price)) || Number(item.price) < 0) return invalid(`item-price-${index}`, '单价必须为非负数。')
    if (!Number.isFinite(Number(item.expectedQty || 0)) || Number(item.expectedQty || 0) < 0) return invalid(`item-expected-${index}`, '应收数量必须为非负数。')
    if (form.taxEnabled && (!Number.isFinite(Number(item.taxRate)) || Number(item.taxRate) < 0 || Number(item.taxRate) > 100)) return invalid(`item-tax-${index}`, '税率必须在 0 到 100 之间。')
  }
  const unmatchedIndex = form.items.findIndex(item => item.goodsName && !item.productId)
  if (unmatchedIndex !== -1) return invalid(`item-product-${unmatchedIndex}`, '请从物料列表选择有效物料。')
  return ''
}

export function purchaseOrderPayload(form, status = 'pending') {
  const hasValue = value => value !== '' && value != null
  return {
    orderNo: form.orderNo,
    orderDate: form.orderDate,
    expectedDate: form.expectedDate,
    storeId: Number(form.storeId),
    supplierId: null,
    remark: form.remark,
    status,
    items: form.items.filter(item => item.productId).map(item => ({
      orderItemId: item.orderItemId,
      productId: Number(item.productId),
      productCode: item.productCode,
      productName: item.goodsName,
      warehouseId: item.warehouseId ? Number(item.warehouseId) : null,
      specification: item.specification,
      unit: item.unit,
      orderedQty: Number(item.quantity),
      supplierId: item.supplierId ? Number(item.supplierId) : null,
      unitPrice: hasValue(item.price) ? Number(item.price) : null,
      amount: hasValue(item.amount) ? Number(item.amount) : null,
      remark: item.remark
    }))
  }
}

export function validatePurchaseOrder(form, audit = false, onInvalid = () => {}) {
  const invalid = (key, message) => { onInvalid(key, message); return message }
  const hasValue = value => value !== '' && value != null
  if (!form.storeId) return invalid('storeId', '请选择申请门店。')
  if (!form.orderDate) return invalid('documentDate', '请填写申请日期。')
  if (!form.items.some(item => item.productId)) return invalid('item-product-0', '请至少选择一条原材料。')
  for (const [index, item] of form.items.entries()) {
    if (!item.productId) continue
    if (!Number.isFinite(Number(item.quantity)) || Number(item.quantity) <= 0) return invalid(`item-quantity-${index}`, '采购数量必须大于 0。')
    if (audit && !item.supplierId) return invalid(`item-supplier-${index}`, '审核前请为每项物料补充采购供应商。')
    if (audit && !hasValue(item.price)) return invalid(`item-price-${index}`, '审核前请为每项物料补充采购单价。')
    if (hasValue(item.price) && (!Number.isFinite(Number(item.price)) || Number(item.price) < 0)) return invalid(`item-price-${index}`, '采购单价必须为非负数。')
    if (hasValue(item.amount) && (!Number.isFinite(Number(item.amount)) || Number(item.amount) < 0)) return invalid(`item-amount-${index}`, '金额必须为非负数。')
  }
  return ''
}

export function inboundAmounts(item, taxEnabled) {
  const base = (Number(item.quantity) || 0) * (Number(item.price) || 0)
  const taxAmount = Number((base * (taxEnabled ? Number(item.taxRate) || 0 : 0) / 100).toFixed(2))
  return { amount: Number(base.toFixed(2)), taxAmount, taxIncludedAmount: Number((base + taxAmount).toFixed(2)), taxIncludedPrice: Number(((Number(item.price) || 0) * (1 + (taxEnabled ? Number(item.taxRate) || 0 : 0) / 100)).toFixed(4)) }
}
