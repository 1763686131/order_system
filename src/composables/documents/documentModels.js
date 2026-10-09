export const DOCUMENT_TYPES = Object.freeze({
  sale: { title: '销售订单', partyLabel: '客户', partyField: 'customerId', dateField: 'orderDate', numberField: 'orderNumber', remarkField: 'orderRemark', specField: 'spec', includedField: 'totalAmount', printType: 'sale', showPackages: true },
  'sale-return': { title: '销售退货单', partyLabel: '客户', partyField: 'customerId', dateField: 'returnDate', numberField: 'returnNumber', remarkField: 'remark', specField: 'specification', includedField: 'taxIncludedAmount', printType: 'return', showPackages: true },
  purchase: { title: '进货单', partyLabel: '供应商', partyField: 'supplierId', dateField: 'documentDate', numberField: 'documentNo', remarkField: 'remark', specField: 'specification', includedField: 'taxIncludedAmount', printType: 'purchase', showPackages: false },
  'purchase-order': { title: '采购申请', dateLabel: '申请日期', dateField: 'orderDate', numberField: 'orderNo', remarkField: 'remark', specField: 'specification', showPackages: false },
  'purchase-return': { title: '采购退货单', partyLabel: '供应商', partyField: 'supplierId', dateLabel: '退货日期', dateField: 'businessDate', numberField: 'documentNo', remarkField: 'remark', showPackages: false }
})

export const DOCUMENT_ACTIONS = ['create', 'edit', 'copy', 'view', 'audit']
export const localDate = () => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}
export const money = value => Number(value || 0).toFixed(2)
export const isLockedInbound = status => ['reviewed', 'posted', 'cancelled', 'red-flushed'].includes(status)
export const canEditReceivedPurchaseInbound = document => document.documentSource === 'other'
  && !document.purchaseOrderId
  && !document.procurementAuditedAt
  && Number(document.payableCount || 0) === 0
  && ['reviewed', 'posted'].includes(document.status)

// Keep inbound wire fields separate from sales/return fields, even where labels match.
export function purchasePayload(form) {
  const type = form.type === 'finished-product' ? 'finished-product' : 'raw-material'
  return {
    documentNo: form.documentNo,
    documentDate: form.documentDate,
    type,
    documentSource: form.purchaseOrderId ? 'purchase-order' : 'other',
    settlementType: form.purchaseOrderId ? 'none' : 'pending_supplier',
    settlementRemark: form.settlementRemark || '',
    postOnSave: !form.purchaseOrderId,
    ...(form.version ? { version: form.version } : {}),
    storeId: Number(form.storeId),
    supplierId: form.purchaseOrderId && type === 'raw-material' && form.supplierId ? Number(form.supplierId) : null,
    purchaseOrderId: form.purchaseOrderId ? Number(form.purchaseOrderId) : null,
    warehouseId: Number(form.warehouseId),
    inspector: form.inspector,
    qualityNo: form.qualityNo,
    remark: form.remark,
    attachments: form.attachments || [],
    status: 'draft',
    items: form.items.filter(item => item.productId).map(item => ({
      productId: Number(item.productId),
      productType: item.productType || type,
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
  const isRawMaterial = form.type !== 'finished-product'
  const itemLabel = isRawMaterial ? '物料' : '商品'
  if (!form.storeId) return invalid('storeId', '请选择门店。')
  if (!form.warehouseId) return invalid('warehouseId', '请选择仓库。')
  if (!form.documentDate) return invalid('documentDate', '请选择单据日期。')
  const items = form.items.filter(item => item.productId)
  if (!items.length) return invalid('item-product-0', `请至少选择一条${itemLabel}。`)
  for (const [index, item] of form.items.entries()) {
    if (!item.productId) continue
    if (!Number.isFinite(Number(item.quantity)) || Number(item.quantity) <= 0) return invalid(`item-quantity-${index}`, '实收数量必须大于 0。')
    if (!item.batchNo?.trim()) return invalid(`item-batch-${index}`, `请填写${itemLabel}的批次号。`)
    if (form.purchaseOrderId && (!Number.isFinite(Number(item.price)) || Number(item.price) < 0)) return invalid(`item-price-${index}`, '单价必须为非负数。')
    if (!Number.isFinite(Number(item.expectedQty || 0)) || Number(item.expectedQty || 0) < 0) return invalid(`item-expected-${index}`, '应收数量必须为非负数。')
    if (form.taxEnabled && (!Number.isFinite(Number(item.taxRate)) || Number(item.taxRate) < 0 || Number(item.taxRate) > 100)) return invalid(`item-tax-${index}`, '税率必须在 0 到 100 之间。')
  }
  const unmatchedIndex = form.items.findIndex(item => item.goodsName && !item.productId)
  if (unmatchedIndex !== -1) return invalid(`item-product-${unmatchedIndex}`, `请从${itemLabel}列表选择有效${itemLabel}。`)
  return ''
}

export function purchaseOrderPayload(form, status = 'pending') {
  const hasValue = value => value !== '' && value != null
  return {
    orderNo: form.orderNo,
    ...(form.version ? { version: form.version } : {}),
    orderDate: form.orderDate,
    expectedDate: form.expectedDate,
    storeId: Number(form.storeId),
    supplierId: null,
    purchaser: form.purchaser || '',
    creator: form.creator || '',
    paymentAmount: hasValue(form.paymentAmount) ? Number(form.paymentAmount) : null,
    otherFees: hasValue(form.otherFees) ? Number(form.otherFees) : 0,
    settlementAccount: form.settlementAccount || '',
    invoiceRequired: Boolean(form.invoiceRequired),
    paymentMethod: form.paymentMethod || '',
    paymentAccountId: form.paymentAccountId ? Number(form.paymentAccountId) : null,
    currentPayment: hasValue(form.currentPayment) ? Number(form.currentPayment) : 0,
    remark: form.remark,
    status,
    items: form.items.filter(item => item.productId).map(item => ({
      orderItemId: item.orderItemId,
      productType: item.productType || 'raw-material',
      productId: Number(item.productId),
      productCode: item.productCode,
      productName: item.goodsName,
      categoryId: item.categoryId ? Number(item.categoryId) : null,
      categoryName: item.categoryName || '',
      warehouseId: item.warehouseId ? Number(item.warehouseId) : null,
      specification: item.specification,
      unit: item.unit,
      orderedQty: Number(item.quantity),
      actualPurchaseQty: hasValue(item.actualQuantity) ? Number(item.actualQuantity) : null,
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
  if (hasValue(form.paymentAmount) && (!Number.isFinite(Number(form.paymentAmount)) || Number(form.paymentAmount) < 0)) {
    return invalid('paymentAmount', '折后金额必须为非负数。')
  }
  if (hasValue(form.otherFees) && (!Number.isFinite(Number(form.otherFees)) || Number(form.otherFees) < 0)) {
    return invalid('otherFees', '其它费用必须为非负数。')
  }
  if (hasValue(form.currentPayment) && (!Number.isFinite(Number(form.currentPayment)) || Number(form.currentPayment) < 0)) {
    return invalid('currentPayment', '已付金额必须为非负数。')
  }
  if (Number(form.currentPayment || 0) > 0 && !form.paymentMethod) return invalid('paymentMethod', '填写已付金额时请选择付款方式。')
  if (Number(form.currentPayment || 0) > 0 && form.paymentMethod === 'bank_transfer' && !form.paymentAccountId) {
    return invalid('paymentAccountId', '请选择对公付款账户。')
  }
  if (Number(form.currentPayment || 0) > 0 && form.paymentMethod === 'other' && !String(form.settlementAccount || '').trim()) {
    return invalid('settlementAccount', '请填写其它付款方式说明。')
  }
  if (!form.items.some(item => item.productId)) return invalid('item-product-0', '请至少选择一条商品。')
  for (const [index, item] of form.items.entries()) {
    if (!item.productId) continue
    if (!Number.isFinite(Number(item.quantity)) || Number(item.quantity) <= 0) return invalid(`item-quantity-${index}`, '申请数量必须大于 0。')
    if (audit && !hasValue(item.actualQuantity)) return invalid(`item-actual-quantity-${index}`, '审核前请为每项物料补充实际采购数量。')
    if (hasValue(item.actualQuantity) && (!Number.isFinite(Number(item.actualQuantity)) || Number(item.actualQuantity) <= 0)) {
      return invalid(`item-actual-quantity-${index}`, '实际采购数量必须大于 0。')
    }
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

export const purchaseReturnStatusLabels = {
  draft: '草稿', audited: '已审核', reversed: '已反审核', cancelled: '已取消'
}

export function purchaseReturnOriginalCost(item) {
  const unitPriceCents = Math.round(Number(item.originalUnitPrice || 0) * 100)
  return Math.round(unitPriceCents * Number(item.quantity || 0)) / 100
}

export function purchaseReturnPayload(form) {
  return {
    supplierId: Number(form.supplierId),
    storeId: Number(form.storeId),
    businessDate: form.businessDate,
    remark: form.remark || '',
    ...(form.version ? { version: form.version } : {}),
    items: form.items.filter(item => item.inboundItemId).map(item => ({
      inboundItemId: Number(item.inboundItemId),
      quantity: Number(item.quantity),
      returnAmount: Number(item.returnAmount),
      differenceReason: item.differenceReason?.trim() || ''
    }))
  }
}

export function validatePurchaseReturn(form, sources, onInvalid = () => {}) {
  const invalid = (key, message) => { onInvalid(key, message); return message }
  const hasValue = value => value !== '' && value != null
  if (!form.storeId) return invalid('storeId', '请选择门店。')
  if (!form.supplierId) return invalid('supplierId', '请选择供应商。')
  if (!form.businessDate) return invalid('documentDate', '请选择退货日期。')
  const items = form.items.filter(item => item.inboundItemId)
  if (!items.length) return invalid('item-source-0', '请至少选择一条来源入库明细。')
  if (items.length > 300) return invalid('item-source-0', '退货明细不能超过 300 项。')
  const seen = new Set()
  for (const [index, item] of form.items.entries()) {
    if (!item.inboundItemId) {
      if (hasValue(item.quantity) || hasValue(item.returnAmount) || item.differenceReason?.trim()) {
        return invalid(`item-source-${index}`, '请先选择来源入库明细。')
      }
      continue
    }
    const source = sources.find(row => Number(row.inboundItemId) === Number(item.inboundItemId))
    if (!source) return invalid(`item-source-${index}`, '来源入库明细已不可退，请刷新批次后重新选择。')
    if (seen.has(Number(item.inboundItemId))) return invalid(`item-source-${index}`, '同一入库明细不能重复选择。')
    seen.add(Number(item.inboundItemId))
    if (!hasValue(item.quantity) || !Number.isFinite(Number(item.quantity)) || Number(item.quantity) <= 0) {
      return invalid(`item-quantity-${index}`, '退货数量必须大于 0。')
    }
    if (Number(item.quantity) > Number(source.availableQuantity)) {
      return invalid(`item-quantity-${index}`, '退货数量不能超过该批次可退数量或当前库存。')
    }
    if (!hasValue(item.returnAmount) || !Number.isFinite(Number(item.returnAmount)) || Number(item.returnAmount) < 0) {
      return invalid(`item-return-amount-${index}`, '确认退货金额必须为非负数。')
    }
    if (Math.round(purchaseReturnOriginalCost({ originalUnitPrice: source.originalUnitPrice, quantity: item.quantity }) * 100) !== Math.round(Number(item.returnAmount) * 100)
      && !item.differenceReason?.trim()) {
      return invalid(`item-difference-${index}`, '退货金额与原成本不一致时必须填写差异原因。')
    }
  }
  return ''
}
