export const DOCUMENT_TYPES = Object.freeze({
  sale: { title: '销售订单', partyLabel: '客户', partyField: 'customerId', dateField: 'orderDate', numberField: 'orderNumber', remarkField: 'orderRemark', specField: 'spec', includedField: 'totalAmount', printType: 'sale', showPackages: true },
  'sale-return': { title: '销售退货单', partyLabel: '客户', partyField: 'customerId', dateField: 'returnDate', numberField: 'returnNumber', remarkField: 'remark', specField: 'specification', includedField: 'taxIncludedAmount', printType: 'return', showPackages: true },
  purchase: { title: '进货单', partyLabel: '供应商', partyField: 'supplierId', dateField: 'documentDate', numberField: 'documentNo', remarkField: 'remark', specField: 'specification', includedField: 'taxIncludedAmount', printType: 'purchase', showPackages: false }
})

export const DOCUMENT_ACTIONS = ['create', 'edit', 'copy', 'view']
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
    supplierId: Number(form.supplierId),
    warehouseId: Number(form.warehouseId),
    inspector: form.inspector,
    qualityNo: form.qualityNo,
    remark: form.remark,
    attachments: form.attachments || [],
    status: 'draft',
    items: form.items.filter(item => item.productId).map(item => ({
      productId: Number(item.productId),
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

export function validatePurchase(form) {
  if (!form.storeId || !form.supplierId || !form.warehouseId) return '请选择门店、供应商和仓库'
  if (!form.documentDate) return '请选择单据日期'
  const items = form.items.filter(item => item.productId)
  if (!items.length) return '请至少选择一条物料'
  for (const item of items) {
    if (!Number.isFinite(Number(item.quantity)) || Number(item.quantity) <= 0) return '实收数量必须大于 0'
    if (!item.batchNo?.trim()) return '请填写每条物料的批次号'
    if (!Number.isFinite(Number(item.price)) || Number(item.price) < 0) return '单价必须为非负数'
    if (!Number.isFinite(Number(item.expectedQty || 0)) || Number(item.expectedQty || 0) < 0) return '应收数量必须为非负数'
    if (form.taxEnabled && (!Number.isFinite(Number(item.taxRate)) || Number(item.taxRate) < 0 || Number(item.taxRate) > 100)) return '税率必须在 0 到 100 之间'
  }
  if (form.items.some(item => item.goodsName && !item.productId)) return '请从物料列表选择有效物料'
  return ''
}

export function inboundAmounts(item, taxEnabled) {
  const base = (Number(item.quantity) || 0) * (Number(item.price) || 0)
  const taxAmount = Number((base * (taxEnabled ? Number(item.taxRate) || 0 : 0) / 100).toFixed(2))
  return { amount: Number(base.toFixed(2)), taxAmount, taxIncludedAmount: Number((base + taxAmount).toFixed(2)), taxIncludedPrice: Number(((Number(item.price) || 0) * (1 + (taxEnabled ? Number(item.taxRate) || 0 : 0) / 100)).toFixed(4)) }
}
