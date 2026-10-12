export const invoiceLabels = {
  not_required: '无需开票', unbilled: '未开票', partial: '部分开票',
  billed: '已开票', difference: '开票有差异'
}
export const paymentLabels = {
  not_confirmed: '尚未确认应付', unpaid: '未付款', partial: '部分付款', paid: '已结清'
}
export const settlementLabels = {
  not_required: '无需结算', pending_inbound: '待入库确认',
  pending_supplier: '待补采购信息', supplier_assigned: '待审核确认',
  payable_confirmed: '应付已确认'
}
export const businessLabels = {
  INITIAL: '期初余额', PURCHASE_INBOUND: '采购入账',
  INDEPENDENT_PURCHASE_INBOUND: '独立入库应付',
  PURCHASE_INBOUND_REVERSAL: '采购入账冲销',
  INDEPENDENT_PURCHASE_INBOUND_REVERSAL: '独立入库冲销',
  PAYMENT: '供应商付款单', ADVANCE_PAYMENT: '新增供应商预付款',
  PREPAYMENT_ALLOCATION: '预付款核销', CREDIT_ALLOCATION: '贷项核销',
  PAYMENT_REVERSAL: '付款核销冲销', ADVANCE_PAYMENT_REVERSAL: '预付款冲销',
  PREPAYMENT_ALLOCATION_REVERSAL: '预付款核销冲销', CREDIT_ALLOCATION_REVERSAL: '贷项核销冲销',
  PURCHASE_RETURN: '采购退货', PURCHASE_RETURN_ADJUSTMENT: '退货价格调整',
  SUPPLIER_REFUND: '供应商退款', SUPPLIER_REFUND_REVERSAL: '供应商退款冲销',
  PURCHASE_RETURN_REVERSAL: '采购退货冲销', PURCHASE_RETURN_ADJUSTMENT_REVERSAL: '退货价格调整冲销'
}
export const documentStatusLabels = { draft: '草稿', audited: '已审核', confirmed: '已确认', reversed: '已撤销', cancelled: '已作废' }

export function invoiceSourceKey(row) {
  return row.sourceType === 'purchase_order'
    ? `order-item-${row.purchaseOrderItemId}`
    : String(row.payableTransactionId ?? row.id)
}
export const formatMoney = value => Number(value || 0).toLocaleString('zh-CN', {
  minimumFractionDigits: 2, maximumFractionDigits: 2
})
export function formatTableMoney(value, currency = '') {
  const amount = Number(value) || 0
  return Math.round(Math.abs(amount) * 100) === 0 ? '-' : `${currency}${formatMoney(amount)}`
}
export const operationKey = () => globalThis.crypto?.randomUUID?.()
  || `op-${Date.now()}-${Math.random().toString(16).slice(2)}`
export const sumMoney = (rows, field) => rows.reduce((total, row) => total + Math.round(Number(row[field] || 0) * 100), 0) / 100
export function paymentAllocationPreview(sources, paymentAmount, businessDate) {
  let remaining = Math.max(0, Math.round(Number(paymentAmount || 0) * 100))
  const result = []
  const ordered = sources.filter(row => !row.lockedAt && row.businessDate <= businessDate)
    .slice().sort((left, right) => left.businessDate.localeCompare(right.businessDate) || Number(left.id) - Number(right.id))
  for (const row of ordered) {
    const allocated = Math.min(remaining, Math.max(0, Math.round(Number(row.availableAmount || 0) * 100)))
    if (allocated > 0) {
      result.push({
        payableTransactionId: row.id, documentNo: row.documentNo, productName: row.productName,
        businessDate: row.businessDate, invoiceStatus: row.invoiceStatus,
        payableAmount: row.payableAmount ?? row.amountIncludingTax, amount: allocated / 100
      })
      remaining -= allocated
    }
    if (remaining === 0) break
  }
  return result
}
export function fulfillmentLabel(record) {
  if (record.progressBasis === 'lines') return `${record.completedLineCount || 0} / ${record.totalLineCount || 0} 行`
  return `${record.receivedQuantity || 0} / ${record.totalQuantity || 0}${record.items?.[0]?.unit || ''}`
}
