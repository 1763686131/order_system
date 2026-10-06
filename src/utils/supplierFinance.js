export const invoiceLabels = {
  not_required: '无需开票', unbilled: '未开票', partial: '部分开票',
  billed: '已开票', difference: '开票有差异'
}
export const paymentLabels = {
  not_confirmed: '尚未确认应付', unpaid: '未付款', partial: '部分付款', paid: '已结清'
}
export const settlementLabels = {
  not_required: '无需结算', pending_inbound: '待入库确认',
  pending_supplier: '待补供应商', supplier_assigned: '已补供应商/待确认',
  payable_confirmed: '应付已确认'
}
export const businessLabels = {
  INITIAL: '期初余额', PURCHASE_INBOUND: '采购入账',
  INDEPENDENT_PURCHASE_INBOUND: '独立入库应付',
  PURCHASE_INBOUND_REVERSAL: '采购入账冲销',
  INDEPENDENT_PURCHASE_INBOUND_REVERSAL: '独立入库冲销'
}
export const formatMoney = value => Number(value || 0).toLocaleString('zh-CN', {
  minimumFractionDigits: 2, maximumFractionDigits: 2
})
export const operationKey = () => crypto.randomUUID()
export function fulfillmentLabel(record) {
  if (record.progressBasis === 'lines') return `${record.completedLineCount || 0} / ${record.totalLineCount || 0} 行`
  return `${record.receivedQuantity || 0} / ${record.totalQuantity || 0}${record.items?.[0]?.unit || ''}`
}
