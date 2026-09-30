import { computed, reactive } from 'vue'
import { DOCUMENT_TYPES } from './documentModels'
import { useSalesDocument } from './useSalesDocument'
import { useReturnDocument } from './useReturnDocument'
import { usePurchaseDocument } from './usePurchaseDocument'

export function useBusinessDocument(props) {
  const config = DOCUMENT_TYPES[props.documentType]
  if (!config) throw new Error(`Unknown document type: ${props.documentType}`)
  if (props.documentType === 'purchase') return reactive({ ...usePurchaseDocument(props), config })
  const sale = props.documentType === 'sale'
  const state = sale
    ? useSalesDocument({ orderId: ['edit', 'view'].includes(props.action) ? props.documentId : null, action: props.action })
    : useReturnDocument({ returnId: props.documentId, productType: props.productType, action: props.action })
  const form = sale ? state.formData : state.form
  return reactive({
    ...state,
    config: computed(() => ({ ...config, title: !sale && state.productType.value === 'raw-material' ? '原材料退货单' : config.title })),
    form,
    readOnly: state.readOnly,
    loading: state.loading,
    loadFailed: state.loadFailed,
    taxEnabled: sale ? state.showTaxColumns : computed({ get: () => form.value.taxEnabled, set: value => { form.value.taxEnabled = value } }),
    activeProductRow: sale ? state.activeProductRow : state.activeProductItem,
    getProductStock: sale ? product => Number(product.stock || 0) : state.getProductStock,
    setCustomerInputRef: sale ? state.setCustomerInputRef : element => { state.customerInputRef.value = element },
    setCustomerDropdownRef: element => { state.customerDropdownRef.value = element },
    setProductDropdownRef: element => { if (state.productDropdownRef) state.productDropdownRef.value = element },
    onProductInput: state.handleProductInput,
    onPackagesInput: sale ? state.onPackagesChange : index => state.onPackagesChange(form.value.items[index]),
    onQuantityInput: sale ? state.onQuantityChange : index => state.onQuantityChange(form.value.items[index]),
    onPriceInput: sale ? state.onPriceChange : index => state.calculateRow(form.value.items[index]),
    onTaxRateInput: sale ? state.onItemTaxRateChange : index => state.calculateRow(form.value.items[index]),
    onIncludedPriceInput: sale ? state.onTaxIncludedPriceChange : index => state.calculateFromTaxIncluded(form.value.items[index]),
    totalIncludedAmount: sale ? state.totalTaxAmount : state.totalTaxIncludedAmount,
    notice: sale ? computed(() => ({ ...state.saveToast.value, type: 'success' })) : state.notice,
    save: sale ? state.handleSaveAndPrint : state.save,
    clearForm: sale ? state.confirmClear : state.clearForm,
    close: sale ? state.confirmClose : state.close,
    printVariables: sale ? computed(() => state.printOrderVariables.value || state.orderPrintVariables.value) : state.returnPrintVariables,
    printNumber: sale ? computed(() => state.printOrderVariables.value?.orderNumber || form.value.orderNumber) : computed(() => form.value.returnNumber),
    closePrintPreview: sale ? state.closeOrderPrintPreview : state.closePrintPreview
  })
}
