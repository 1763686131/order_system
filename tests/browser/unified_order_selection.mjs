import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

// Run from the repository root: node tests/browser/unified_order_selection.mjs [scenario]
// Scenarios: default, reordered, reordered-hidden, reordered-legacy, reordered-mobile, reordered-persistence, inline-mobile, inline-tax-mobile.
const root = fileURLToPath(new URL('../../', import.meta.url))
const scenario = process.argv[2] || 'reordered-hidden'
const browserPath = [
  process.env.CHROME_BIN,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/chromium',
  '/usr/bin/google-chrome'
].find(path => path && existsSync(path))
if (!browserPath) throw new Error('Set CHROME_BIN to an installed Chromium browser to run this test')

const html = `<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>
body { margin: 0; }
.test-header { height: 60px; }
.main-content { height: 500px; padding: 20px; overflow-y: auto; }
</style></head><body><div id="app"></div><pre id="result">pending</pre>
<script type="module">
import { createApp, h, ref, nextTick } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createMemoryHistory, RouterView } from 'vue-router'
import OrderList from '/src/views/admin/sales/UnifiedOrderList.vue'
import tableLayout from '/src/directives/tableLayout.js'
import { provideAdminStickyPanel } from '/src/composables/useAdminStickyPanel.js'
import { useUserStore } from '/src/stores/user.js'
import { useOrderSelectionStore } from '/src/stores/orderSelection.js'
import request from '/src/api/request.js'

const results = { errors: [], calls: [], scroll: [] }
if (location.search.includes('legacy')) Element.prototype.moveBefore = undefined
if (location.search.includes('reordered')) {
  localStorage.setItem('table-column-order:sales-finance-list', JSON.stringify([
    'selection', 'status', 'actions', 'customer', 'date', 'order-number'
  ]))
  localStorage.setItem('table-column-widths:sales-finance-list', JSON.stringify({ date: 150, goods: 200 }))
}
if (location.search.includes('hidden')) {
  localStorage.setItem('table-column-hidden:sales-finance-list', JSON.stringify(['phone', 'address']))
}
window.addEventListener('error', event => results.errors.push(event.message))
window.addEventListener('unhandledrejection', event => results.errors.push(String(event.reason)))
const pause = () => new Promise(resolve => setTimeout(resolve, 50))
const frame = () => new Promise(resolve => requestAnimationFrame(resolve))
const settle = async () => { await nextTick(); await frame(); await frame(); await pause() }
const assert = (condition, message) => { if (!condition) throw new Error(message) }
let orderData = Array.from({ length: 40 }, (_, index) => ({
  id: index + 1, order_number: 'TEST-' + (index + 1),
  order_client: 'Test customer', store_id: 1,
  date: '2026-10-29', status: 'shipped', audit_state: index % 2,
  order_goods: [{ product_id: 1, product_name: 'Test product', quantity: 1, price: 10 }],
  total_amount: 10
}))
const inline = location.search.includes('inline')
const taxed = location.search.includes('inline-tax')
if (inline) {
  orderData = orderData.map(order => ({
    ...order,
    customer_id: 9, warehouse_id: 1,
    contact_person: 'Original contact', contact_phone: '13800000000', contact_address: 'Original address',
    project_name: 'Keep project', goods_packaging: 'Keep packaging',
    logistics_service: '用户自提', sales_person: 'Keep salesperson', settlement_account: 'Keep account',
    total_packages: 7, discount_amount: 8, other_fees: 2, should_receive: 10,
    current_payment: 1, current_debt: 9, remark: 'Original remark',
    order_goods: [{
      product_id: 1, goods_name: 'Test product', spec: 'Original spec', unit: 'kg', warehouse_id: 1,
      packages: 1, quantity: 1, price: 10, amount: 10, remark: 'Keep item remark',
      tax_rate: taxed ? 13 : 0, tax_included_price: taxed ? 11.3 : 0, total_amount: taxed ? 11.3 : 0
    }]
  }))
}
let failOrders = false
let delayOrders = false
let failSave = false
let saveAttempts = 0
const editPayloads = []
request.defaults.adapter = async config => {
  results.calls.push([config.method, config.url])
  let data = []
  if (config.url === '/orders') {
    if (delayOrders) await new Promise(resolve => setTimeout(resolve, 400))
    if (failOrders) throw new Error('Simulated order refresh failure')
    data = orderData
  }
  if (config.url === '/stores') data = [{ id: 1, name: 'Test store', status: 'active' }]
  if (inline && config.url === '/warehouses') data = [
    { id: 1, storeId: 1, name: 'Test warehouse' }, { id: 2, storeId: 2, name: 'Other warehouse' }
  ]
  if (inline && config.url === '/products/units/measurements') data = [{ id: 1, name: 'kg' }]
  if (inline && config.url === '/products/inventory') data = [
    { id: 1, code: 'SKU-001', name: 'Test product', specification: 'Original spec', unitId: 1, price: 10, storeIds: [1], warehouseId: 1 },
    { id: 2, code: 'SKU-002', name: 'Added product', specification: 'Added spec', unitId: 1, price: 5, storeIds: [1], warehouseId: 1, unitConversions: [{ value: 2 }] },
    { id: 3, code: 'SKU-003', name: 'Other store product', unitId: 1, price: 100, storeIds: [2], warehouseId: 2 },
    { id: 4, code: 'SKU-004', name: 'Other warehouse product', unitId: 1, price: 100, storeIds: [1], warehouseId: 2 }
  ]
  if (inline && config.url === '/orders/1' && config.method === 'put') {
    saveAttempts++
    const payload = JSON.parse(config.data)
    editPayloads.push(payload)
    await new Promise(resolve => setTimeout(resolve, 150))
    if (failSave) {
      const error = new Error('Simulated save failure')
      error.response = { data: { message: 'Save failed; retry' } }
      throw error
    }
    const updated = {
      ...orderData[0],
      contact_person: payload.contactPerson, contact_phone: payload.contactPhone, contact_address: payload.contactAddress,
      remark: payload.orderRemark, total_packages: payload.totalPackages, discount_amount: payload.discountAmount,
      other_fees: payload.otherFees, current_payment: payload.currentPayment,
      should_receive: payload.discountAmount + payload.otherFees,
      current_debt: payload.discountAmount + payload.otherFees - payload.currentPayment,
      order_goods: payload.items.map(item => ({
        product_id: item.productId, goods_name: item.goodsName, spec: item.spec, unit: item.unit,
        warehouse_id: item.warehouseId, packages: item.packages, quantity: item.quantity,
        price: item.price, amount: item.amount, tax_rate: item.taxRate,
        tax_included_price: item.taxIncludedPrice, total_amount: item.totalAmount, remark: item.remark
      }))
    }
    orderData[0] = updated
    data = { success: true, data: updated }
  }
  return { data, status: 200, statusText: 'OK', headers: {}, config }
}
const pinia = createPinia()
let stickyController
useUserStore(pinia).$patch({ id: 7, isSuperAdmin: true, allStores: true, allWarehouses: true })
const form = {
  render: () => h('button', { class: 'return-to-list', onClick: () => router.push('/') }, 'Return')
}
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'admin-sales', component: OrderList, props: { mode: 'finance' } },
    { path: '/sales/create', name: 'admin-sales-create', component: form },
    { path: '/sales/edit/:id', name: 'admin-sales-edit', component: form },
    { path: '/logistics', name: 'admin-sales-logistics', component: OrderList, props: { mode: 'logistics' } }
  ]
})
await router.push('/')
await router.isReady()
const app = createApp({
  setup() {
    const main = ref(null)
    const header = ref(null)
    const sticky = provideAdminStickyPanel(main, header)
    stickyController = sticky
    return () => h('div', [
      h('header', { class: 'test-header', ref: header }),
      h('main', { class: 'main-content', ref: main, onScroll: sticky.handleScroll }, [
        h(RouterView)
      ])
    ])
  }
})
app.use(pinia).use(router).directive('table-layout', tableLayout)
app.config.errorHandler = error => results.errors.push(String(error.stack || error))
app.mount('#app')
const waitForOrders = async () => {
  for (let count = 0; count < 100 && document.querySelectorAll('.record-row').length < 30; count++) await pause()
  await settle()
  assert(document.querySelectorAll('.record-row').length === 30, 'Orders must finish loading')
}
const findOrderRow = id => [...document.querySelectorAll('.record-row')].find(row =>
  row.querySelector('[data-column-key="order-number"]')?.textContent.trim() === 'TEST-' + id
)
const checkInlineEditing = async () => {
  const card = () => document.querySelectorAll('.mobile-order-card')[0]
  const editor = () => card().querySelector('.mobile-order-editor')
  const dialog = () => document.querySelector('.mobile-product-dialog')
  const setValue = async (element, value, event = 'input') => {
    element.value = value
    element.dispatchEvent(new Event(event, { bubbles: true }))
    await settle()
  }
  const field = name => editor().querySelector('[aria-label="' + name + '"]')
  const productField = name => dialog().querySelector('[aria-label="' + name + '"]')
  const productOptions = () => [...dialog().querySelectorAll('[role="option"]')]
  const searchProducts = async query => {
    productField('商品').focus()
    await setValue(productField('商品'), query)
  }
  const chooseProduct = async (id, query = 'SKU-00' + id) => {
    await searchProducts(query)
    const option = productOptions().find(option => option.dataset.productId === String(id))
    assert(option, 'Searching must show the requested product')
    option.click()
    await settle()
    assert(!dialog().querySelector('[role="listbox"]'), 'Selecting a product must close its search results')
  }
  const productKey = async (key, options = {}) => {
    productField('商品').dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, ...options }))
    await settle()
  }
  const row = index => card().querySelectorAll('.mobile-order-product')[index]
  const editProduct = async index => {
    editor().querySelector('[aria-label="修改第' + (index + 1) + '项商品"]').click()
    await settle()
    assert(dialog(), 'Editing a product must open its detail dialog')
  }
  const confirmProduct = async () => {
    dialog().querySelector('form').requestSubmit()
    await settle()
    assert(!dialog(), 'Confirming valid product details must close the dialog')
    assert(saveAttempts === 0, 'Product confirmation must never submit the order')
  }
  const captureVisual = async name => {
    if (!location.search.includes('visual')) return
    document.querySelector('.main-content').style.height = 'auto'
    document.querySelector('.main-content').scrollTop = 0
    document.querySelectorAll('.mobile-order-card').forEach((element, index) => {
      if (index) element.style.display = 'none'
    })
    await settle()
    window.inlineScreenshotName = name
    window.inlineScreenshotClip = { x: 0, y: 0, width: innerWidth, height: dialog() ? innerHeight : document.documentElement.scrollHeight, scale: 1 }
    await new Promise(resolve => { window.continueInlineTest = resolve })
  }
  card().querySelector('.mobile-order-select input').click()
  card().querySelector('.mobile-order-toggle').click()
  await settle()
  const originalSections = ['.mobile-order-contact-row', '.mobile-order-products', '.mobile-order-summary'].map(selector => card().querySelector(selector))
  const originalProductName = row(0).querySelector('.mobile-order-product-name')
  card().querySelector('.row-menu-trigger').click()
  await settle()
  document.querySelector('.row-action-menu [role="menuitem"]').click()
  await settle()
  assert(router.currentRoute.value.name === 'admin-sales', 'Mobile edit must stay on the list route')
  assert(editor(), 'Mobile edit must show a form inside the original card')
  assert(!document.querySelector('.detail-modal'), 'Mobile menu edit must not open the detail dialog')
  assert(field('收货人').value === 'Original contact', 'Contact information must be prefilled')
  assert(field('应收金额').value === '10', 'Opening edit must preserve the existing discounted receivable')
  assert(originalSections.every(element => element.isConnected), 'Entering edit mode must preserve the original layout containers')
  assert(originalProductName === row(0).querySelector('.mobile-order-product-name'), 'Entering edit mode must preserve the original product summary')
  assert(!editor().querySelector('.mobile-order-products input, .mobile-order-products select'), 'Product summaries must remain read-only in the main card')
  assert(!field('总件数') && !field('折后金额') && !field('其他费用'), 'Editing must not add new finance sections to the card')
  await setValue(field('收货人'), 'Cancelled edit')
  await editProduct(0)
  assert(productField('商品').getAttribute('role') === 'combobox' && productField('商品').value === 'Test product', 'Product search must show the existing selected product')
  productField('商品').click()
  await settle()
  assert(productOptions().length === 2, 'Opening product search must show all products for the current store and warehouse: ' + JSON.stringify({
    options: productOptions().map(option => option.dataset.productId),
    expanded: productField('商品').getAttribute('aria-expanded'),
    disabled: productField('商品').disabled,
    focused: document.hasFocus(),
    active: document.activeElement?.outerHTML
  }))
  assert(!dialog().textContent.includes('Other store product') && !dialog().textContent.includes('Other warehouse product'), 'Product search must enforce store and warehouse filters')
  await captureVisual('product-search')
  const searchResults = dialog().querySelector('[role="listbox"]').getBoundingClientRect()
  assert(searchResults.left >= 0 && searchResults.right <= innerWidth, 'Product search results must fit the mobile viewport')
  await searchProducts('ADDED')
  assert(productOptions().length === 1 && productOptions()[0].dataset.productId === '2', 'Product names must be searchable without case sensitivity')
  await searchProducts('original spec')
  assert(productOptions().length === 1 && productOptions()[0].dataset.productId === '1', 'Product specifications must be searchable')
  await searchProducts('sku-002')
  assert(productOptions().length === 1 && productOptions()[0].dataset.productId === '2', 'Product codes must be searchable')
  await searchProducts('no matching product')
  assert(productOptions().length === 0 && dialog().querySelector('[role="status"]')?.textContent.includes('暂无匹配商品'), 'Empty searches must display a clear no-results state')
  productField('商品备注').focus()
  await settle()
  assert(productField('商品').getAttribute('aria-expanded') === 'false', 'Leaving product search must dismiss the dropdown')
  dialog().querySelector('form').requestSubmit()
  await settle()
  assert(dialog() && dialog().querySelector('.save-error')?.textContent.includes('搜索结果') && saveAttempts === 0, 'Unselected search text must not silently confirm the old product or save an order')
  await productKey('Escape')
  assert(dialog() && productField('商品').value === 'Test product' && productField('数量').value === '1', 'Escape must dismiss search and restore the unchanged product selection')
  dialog().querySelector('.product-search-toggle').click()
  await settle()
  assert(productOptions().length === 2, 'The dropdown toggle must reopen all available products')
  await productKey('ArrowDown')
  const highlightedProduct = productField('商品').getAttribute('aria-activedescendant')
  assert(document.getElementById(highlightedProduct)?.dataset.productId === '2', 'Arrow keys must move through product results')
  await productKey('ArrowUp')
  await productKey('Enter', { isComposing: true })
  assert(productField('商品').getAttribute('aria-expanded') === 'true' && dialog(), 'IME confirmation must not select a result or close the dialog')
  await productKey('Enter')
  assert(dialog() && productField('商品').getAttribute('aria-expanded') === 'false' && saveAttempts === 0, 'Enter must select the highlighted product without submitting the dialog')
  assert(productField('数量').value === '1' && productField('单价').value === '10', 'Reselecting the existing product must preserve its quantity and price')
  await setValue(productField('数量'), '2')
  await confirmProduct()
  assert(row(0).textContent.includes('2kg'), 'Product confirmation must update the local card')
  editor().querySelector('.cancel-button').click()
  await settle()
  assert(!editor() && card().textContent.includes('Original contact'), 'Cancel must discard unsaved changes')
  assert(row(0).textContent.includes('1kg') && !row(0).textContent.includes('2kg'), 'Order cancellation must also discard confirmed product drafts')
  assert(saveAttempts === 0, 'Cancel must not send a save request')

  card().querySelector('.mobile-order-action.is-primary').click()
  await settle()
  document.querySelector('.detail-modal-footer .button-edit').click()
  await settle()
  for (let count = 0; count < 20 && document.querySelector('.detail-modal'); count++) await pause()
  assert(editor() && !document.querySelector('.detail-modal'), 'Editing from mobile detail must return to the inline card')
  assert(router.currentRoute.value.name === 'admin-sales', 'Mobile detail edit must not navigate')
  await setValue(field('收货人'), 'Updated contact')
  await setValue(field('收货电话'), '13900000000')
  await setValue(field('客户地址'), 'Updated address')
  await setValue(field('订单备注'), 'Updated remark')
  await editProduct(0)
  assert(productField('数量').value === '1' && productField('单价').value === '10', 'Product dialog must be prefilled from the selected summary')
  await setValue(productField('数量'), '99')
  assert(row(0).textContent.includes('1kg') && !row(0).textContent.includes('99kg'), 'Unconfirmed product changes must not leak into the card')
  dialog().querySelector('.cancel-button').click()
  await settle()
  assert(!dialog() && row(0).textContent.includes('1kg'), 'Cancelling a product dialog must discard its changes')
  await editProduct(0)
  await setValue(productField('商品备注'), 'Temporary remark')
  await confirmProduct()
  assert(field('应收金额').value === '10', 'Changing only an item remark must retain an existing discount')
  await editProduct(0)
  await setValue(productField('商品备注'), 'Keep item remark')
  await setValue(productField('数量'), '0')
  dialog().querySelector('form').requestSubmit()
  await settle()
  assert(dialog() && saveAttempts === 0 && row(0).textContent.includes('1kg'), 'Invalid product quantity must not modify the card or submit an order')
  await setValue(productField('数量'), '3')
  await setValue(productField('单价'), '12')
  const expectedFirst = taxed ? 40.68 : 36
  assert(!!productField('含税单价') === taxed, 'Tax fields must follow the existing order tax mode')
  await captureVisual('product-dialog')
  const dialogRect = dialog().getBoundingClientRect()
  assert(dialogRect.left >= 0 && dialogRect.right <= innerWidth && dialogRect.top >= 0 && dialogRect.bottom <= innerHeight, 'The product dialog must fit the mobile viewport')
  assert(dialog().scrollWidth <= dialog().clientWidth, 'Product dialog fields must not overflow')
  await confirmProduct()
  assert(row(0).textContent.includes('3kg') && row(0).textContent.includes('¥' + expectedFirst.toFixed(2)), 'Product confirmation must render its new summary')
  assert(Number(field('应收金额').value) === expectedFirst + 2, 'Confirmed product changes must recalculate receivables and retain other fees')
  const heading = editor().querySelector('.mobile-order-products-head').getBoundingClientRect()
  const addButton = editor().querySelector('.mobile-order-add-product').getBoundingClientRect()
  assert(Math.abs(heading.right - addButton.right) < 1, 'Add product must be at the far right of the product heading')
  editor().querySelector('.mobile-order-add-product').click()
  await settle()
  assert(dialog() && !row(1), 'New products must remain in the dialog until confirmed')
  await chooseProduct(2)
  await setValue(productField('件数'), '2')
  dialog().querySelector('.cancel-button').click()
  await settle()
  assert(!row(1) && saveAttempts === 0, 'Cancelling an addition must leave no empty product row')
  editor().querySelector('.mobile-order-add-product').click()
  await settle()
  await chooseProduct(2, 'added spec')
  assert(productField('商品').value === 'Added product' && productField('规格型号').value === 'Added spec' && productField('单价').value === '5', 'Choosing a result must populate product name, specification and price')
  assert(productField('单位').value === 'kg', 'Selecting a new product must populate its unit')
  await setValue(productField('件数'), '2')
  assert(Number(productField('数量').value) === 4, 'Package conversion must update quantity')
  await confirmProduct()
  const expectedTotal = taxed ? 63.28 : 56
  assert(row(1)?.textContent.includes('Added product') && Number(field('应收金额').value) === expectedTotal + 2, 'Confirmed new products must update the card and total')
  await editProduct(1)
  await setValue(productField('数量'), '5')
  dialog().dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
  await settle()
  assert(!dialog() && row(1).textContent.includes('4kg'), 'Escape must cancel product edits')
  editor().querySelector('[aria-label="删除第2项商品"]').click()
  await settle()
  assert(!row(1) && saveAttempts === 0, 'Removing a product must remain a local draft change')
  assert(Number(field('应收金额').value) === expectedFirst + 2, 'Removing a product must recalculate totals')
  assert(editor().querySelector('[aria-label="删除第1项商品"]').disabled, 'Deleting the last product must be prevented')
  editor().querySelector('.mobile-order-add-product').click()
  await settle()
  await chooseProduct(2)
  await setValue(productField('件数'), '2')
  await confirmProduct()
  await setValue(field('应收金额'), '52')
  await setValue(field('已收金额'), '5')
  assert(editor().querySelector('.mobile-order-summary').textContent.includes('¥47.00'), 'Outstanding amount must update immediately')
  assert(card().querySelector('.mobile-order-total').textContent === '¥52.00', 'Card header total must reflect draft edits')
  assert(editor().scrollWidth <= editor().clientWidth, 'The editor must fit the mobile viewport')
  const inputOverflow = [...editor().querySelectorAll('input, select, textarea, button')].some(element => {
    const rect = element.getBoundingClientRect()
    const parent = editor().getBoundingClientRect()
    return rect.left < parent.left - 1 || rect.right > parent.right + 1
  })
  assert(!inputOverflow, 'Editor controls must not overflow their container')
  const cardRect = card().getBoundingClientRect()
  assert(cardRect.left >= 0 && cardRect.right <= innerWidth, 'The mobile card must fit inside the viewport')
  results.viewport = { width: innerWidth, cardWidth: cardRect.width }
  await captureVisual('order-card')

  failSave = true
  editor().requestSubmit()
  editor().requestSubmit()
  await settle()
  assert(editor().querySelector('.save-button').disabled, 'Saving must disable duplicate submissions')
  assert(editor().querySelector('.cancel-button').disabled, 'Saving must keep the editor mounted')
  for (let count = 0; count < 100 && !editor().querySelector('.mobile-order-save-error'); count++) await pause()
  assert(editor().querySelector('.mobile-order-save-error').textContent.includes('Save failed'), 'Save failures must be displayed inline')
  assert(field('收货人').value === 'Updated contact' && row(1)?.textContent.includes('Added product'), 'Save failure must preserve all draft values')
  assert(saveAttempts === 1, 'Repeated submits must send only one request')
  failSave = false
  editor().requestSubmit()
  for (let count = 0; count < 100 && editor(); count++) await pause()
  await settle()
  assert(!editor(), 'Successful save must exit editing')
  assert(card().textContent.includes('Updated contact') && card().textContent.includes('Added product'), 'Saved contact and new product must appear in the card')
  assert(card().textContent.includes('¥52.00') && card().textContent.includes('¥47.00'), 'Saved financial totals must appear in the list')
  assert(card().querySelector('.mobile-order-select input').checked, 'Saving must preserve selected orders')
  const payload = editPayloads.at(-1)
  assert(payload.projectName === 'Keep project' && payload.goodsPackaging === 'Keep packaging', 'Saving must retain hidden project and packaging fields')
  assert(payload.logisticsService === '用户自提' && payload.salesPerson === 'Keep salesperson' && payload.settlementAccount === 'Keep account', 'Saving must retain logistics, salesperson and account metadata')
  assert(payload.customerId === 9 && payload.storeId === 1 && payload.warehouseId === 1, 'Saving must retain order ownership')
  assert(payload.orderDate === '2026-10-29' && payload.orderNumber === 'TEST-1', 'Saving must retain the order date and number')
  assert(payload.items[0].remark === 'Keep item remark' && payload.taxEnabled === taxed, 'Saving must retain item remarks and tax mode')
  assert(payload.totalPackages === 3 && payload.discountAmount === 50 && payload.otherFees === 2, 'Saving must retain fees and calculate packages from confirmed products')
  assert(Math.abs(payload.items[0].amount - 36) < 0.00001 && Math.abs(payload.items[0].totalAmount - (taxed ? 40.68 : 0)) < 0.00001, 'Saving must send recalculated base and tax amounts')
  const auditedCard = document.querySelectorAll('.mobile-order-card')[1]
  auditedCard.querySelector('.mobile-order-toggle').click()
  await settle()
  assert(!auditedCard.querySelector('.row-menu-trigger'), 'Audited orders must not offer modification')
  useUserStore(pinia).$patch({ isSuperAdmin: false, permissions: [] })
  await settle()
  assert(!card().querySelector('.row-menu-trigger'), 'Users without edit permission must not be offered modification')
  useUserStore(pinia).$patch({ isSuperAdmin: true })
  await settle()
  card().querySelector('.row-menu-trigger').click()
  await settle()
  document.querySelector('.row-action-menu [role="menuitem"]').click()
  await settle()
  assert(editor(), 'The saved order must allow editing again')
  await router.push('/logistics')
  await waitForOrders()
  assert(!document.querySelector('.mobile-order-editor'), 'Switching list modes must clear inline editing state')
  assert(results.errors.length === 0, 'Inline editing must not cause Vue runtime errors')
  results.checks = ['original layout preserved', 'inline menu and detail edit', 'order draft cancellation', 'product dialog confirm and cancel', 'local product add and delete', 'no request before final save', 'product name/specification/code search', 'store and warehouse filtering', 'search empty state and selection validation', 'keyboard selection and IME', 'unchanged product preservation', 'package conversion', 'tax totals', 'validation', 'failed save and retry', 'duplicate prevention', 'metadata preservation', 'permissions', 'mobile layout', 'mode switch cleanup']
}
const checkPersistedSelection = async () => {
  const store = useOrderSelectionStore(pinia)
  const selectedIds = () => [...store.selectedIdsFor('finance', 7)].sort((a, b) => a - b)
  const assertSelection = ids => assert(JSON.stringify(selectedIds()) === JSON.stringify(ids), 'The original selected IDs must be preserved')
  if (sessionStorage.getItem('order-selection-test-phase') === 'reload') {
    assertSelection([])
    assert(!findOrderRow(1)?.querySelector('input').checked, 'Browser reload must clear the first checkbox')
    assert(!findOrderRow(2)?.querySelector('input').checked, 'Browser reload must clear audited selections')
    assert(!document.querySelector('.selection-count'), 'Browser reload must clear the selected count')
    assert(!document.querySelector('.records-table thead input').indeterminate, 'Browser reload must reset select-all')
    assert(document.querySelector('.button-delete').disabled, 'Browser reload must disable deletion without a selection')
    sessionStorage.removeItem('order-selection-test-phase')
    results.phase = 'complete'
    return
  }
  findOrderRow(1).querySelector('input').click()
  findOrderRow(2).querySelector('input').click()
  await settle()
  document.querySelector('[title="下一页"]').click()
  await settle()
  findOrderRow(35).querySelector('input').click()
  await settle()
  assertSelection([1, 2, 35])
  document.querySelector('.create-button').click()
  await settle()
  assert(router.currentRoute.value.name === 'admin-sales-create', 'New order must navigate to the form')
  assert(!document.querySelector('.records-table'), 'The list must be unmounted while the form is open')
  assert(!window.refreshUnifiedOrderList, 'Unmounting must remove the stale refresh callback')
  document.querySelector('.return-to-list').click()
  await waitForOrders()
  assertSelection([1, 2, 35])
  assert(findOrderRow(1).querySelector('input').checked, 'Returning from new order must restore checkboxes')
  findOrderRow(1).click()
  await settle()
  document.querySelector('.detail-modal-footer .button-edit').click()
  await settle()
  assert(router.currentRoute.value.name === 'admin-sales-edit', 'Modify must navigate to the edit form')
  orderData = orderData.map(order => order.id === 1 ? { ...order, order_client: 'Edited customer' } : order)
  document.querySelector('.return-to-list').click()
  await waitForOrders()
  assertSelection([1, 2, 35])
  assert(findOrderRow(1).textContent.includes('Edited customer'), 'Returning from edit must show fresh data')
  assert(findOrderRow(1).querySelector('input').checked, 'Returning from edit must restore the checkbox')
  await router.push('/logistics')
  await waitForOrders()
  assert(document.querySelectorAll('.record-row.selected').length === 0, 'Logistics must have its own selection')
  findOrderRow(3).querySelector('input').click()
  await settle()
  await router.push('/')
  await waitForOrders()
  assertSelection([1, 2, 35])
  assert(!findOrderRow(3).querySelector('input').checked, 'Logistics selection must not leak into sales')
  delayOrders = true
  const refresh = window.refreshUnifiedOrderList()
  await settle()
  assert(document.querySelector('.button-delete').disabled, 'Cached selections must not be deletable while data loads')
  await refresh
  delayOrders = false
  failOrders = true
  await window.refreshUnifiedOrderList()
  await settle()
  assertSelection([1, 2, 35])
  document.querySelector('.button-delete').click()
  await settle()
  assert(!document.querySelector('.confirm-dialog'), 'Failed refresh must not allow deleting stale selections')
  failOrders = false
  orderData = orderData.filter(order => order.id !== 35)
  await window.refreshUnifiedOrderList()
  await waitForOrders()
  assertSelection([1, 2])
  document.querySelector('.button-delete').click()
  await settle()
  assert(document.querySelector('.notice-error')?.textContent.includes('反审核'), 'Restoring selections must preserve audit deletion protection')
  assert(!results.calls.some(([method]) => method === 'delete'), 'Persistence tests must never submit a delete')
  sessionStorage.setItem('order-selection-test-phase', 'reload')
  results.phase = 'reload'
}
try {
  await waitForOrders()
  if (inline) {
    await checkInlineEditing()
  } else if (location.search.includes('persistence')) {
    await checkPersistedSelection()
  } else {
  const main = document.querySelector('.main-content')
  const table = document.querySelector('.records-table')
  const inputs = [...table.querySelectorAll('tbody input[type=checkbox]')]
  results.rowCount = inputs.length
  assert(inputs.length === 30, 'Expected 30 displayed orders')
  if (location.search.includes('reordered')) {
    assert(table.querySelectorAll('thead th')[1].dataset.columnKey === 'status', 'Saved column order must be applied')
  }
  const audited = inputs.find(input => input.title.includes('反审核'))
  assert(audited && !audited.disabled, 'Audited orders must be selectable')
  audited.focus()
  audited.click()
  await settle()
  assert(audited.checked, 'Audited order must stay selected')
  const header = table.querySelector('thead input')
  assert(header.indeterminate, 'A partial selection must set the header indeterminate')
  header.click()
  await settle()
  assert(inputs.every(input => input.checked), 'Select-all must include audited orders')
  document.querySelector('.button-delete').click()
  await settle()
  assert(document.querySelector('.notice-error')?.textContent.includes('反审核'), 'Mixed batch delete must require reversing audit')
  assert(!document.querySelector('.confirm-dialog'), 'Locked batch must not open delete confirmation')
  assert(!results.calls.some(([method]) => method === 'delete'), 'Locked batch must not issue DELETE')
  header.click()
  await settle()
  assert(inputs.every(input => !input.checked), 'Select-all must also deselect audited orders')
  const unlocked = inputs.find(input => !input.title.includes('反审核'))
  unlocked.click()
  await settle()
  document.querySelector('.button-delete').click()
  await settle()
  assert(document.querySelector('.confirm-dialog'), 'Unaudited orders must still allow delete confirmation')
  document.querySelector('.confirm-dialog-cancel').click()
  await settle()
  header.click()
  await settle()
  const focusInput = location.search.includes('mobile')
    ? document.querySelectorAll('.mobile-order-select input')[18]
    : inputs[18]
  focusInput.focus()
  await settle()
  results.scroll.push({ step: 'focused', main: main.scrollTop, inner: table.parentElement.scrollTop, panelStyle: document.querySelector('.search-panel-content').getAttribute('style') })
  const scrollStep = Math.max(160, Math.ceil(main.scrollTop / 8))
  for (let index = 0; index < 12; index++) {
    main.scrollTop = Math.max(0, main.scrollTop - scrollStep)
    const intended = main.scrollTop
    stickyController.handleScroll()
    await settle()
    results.scroll.push({ step: index, intended, main: main.scrollTop, inner: table.parentElement.scrollTop, panelStyle: document.querySelector('.search-panel-content').getAttribute('style') })
    assert(Math.abs(main.scrollTop - intended) < 1, 'Scrolling must not jump back to the focused checkbox')
  }
  results.active = document.activeElement === focusInput
  assert(results.active, 'Layout updates must preserve keyboard focus')
  assert(main.scrollTop === 0, 'The list must be able to scroll to the top')
  assert(inputs.every(input => input.checked), 'Scrolling must preserve selected orders')
  const mobileInputs = [...document.querySelectorAll('.mobile-order-select input')]
  const mobileAudited = mobileInputs.find(input => input.title.includes('反审核'))
  assert(mobileAudited && !mobileAudited.disabled, 'Mobile audited orders must be selectable')
  mobileAudited.click()
  await settle()
  assert(!mobileAudited.checked && !audited.checked, 'Mobile selection must update the shared selection')
  assert(header.indeterminate, 'Mobile changes must update the desktop select-all state')
  if (location.search.includes('mobile')) {
    assert(getComputedStyle(document.querySelector('.mobile-order-list')).display !== 'none', 'Mobile view must be displayed')
  }
  assert(!results.calls.some(([method]) => method === 'delete'), 'Tests must never submit a delete')
  assert(results.errors.length === 0, 'Vue must not report runtime errors')
  results.tableStyle = table.getAttribute('style')
  }
  results.pass = true
} catch (error) {
  results.errors.push(String(error.stack || error))
  results.pass = false
}
document.querySelector('#result').textContent = JSON.stringify(results)
app.unmount()
</script></body></html>`

const profile = await mkdtemp(join(tmpdir(), 'order-selection-check-'))
const server = await createServer({
  root,
  server: { host: '127.0.0.1', port: 0, open: false },
  plugins: [{
    name: 'order-selection-check',
    configureServer(server) {
      server.middlewares.use('/__order-selection-check', async (req, res, next) => {
        try {
          res.setHeader('Content-Type', 'text/html; charset=utf-8')
          res.end(await server.transformIndexHtml('/__order-selection-check', html))
        } catch (error) { next(error) }
      })
    }
  }]
})
try {
  await server.listen()
  const port = server.httpServer.address().port
  const child = spawn(browserPath, [
    '--headless', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-extensions',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
    '--user-data-dir=' + profile, '--window-size=' + (scenario.includes('mobile') ? '390,844' : '1600,900'),
    '--remote-debugging-port=0',
    'about:blank'
  ], { windowsHide: true })
  let stderr = ''
  child.stderr.on('data', data => { stderr += data })
  const closed = new Promise((resolve, reject) => {
    child.once('error', reject)
    child.once('close', resolve)
  })
  let socket
  try {
    let debugPort
    for (let count = 0; count < 100 && !debugPort; count++) {
      try {
        debugPort = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0])
      } catch { await new Promise(resolve => setTimeout(resolve, 100)) }
    }
    if (!debugPort) throw new Error('Chrome failed to start: ' + stderr.slice(-3000))
    const targets = await (await fetch('http://127.0.0.1:' + debugPort + '/json/list')).json()
    const page = targets.find(target => target.type === 'page')
    socket = new WebSocket(page.webSocketDebuggerUrl)
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true })
      socket.addEventListener('error', reject, { once: true })
    })
    let nextId = 0
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++nextId
      const receive = event => {
        const response = JSON.parse(event.data)
        if (response.id !== id) return
        socket.removeEventListener('message', receive)
        if (response.error) reject(new Error(JSON.stringify(response.error)))
        else resolve(response.result)
      }
      socket.addEventListener('message', receive)
      socket.send(JSON.stringify({ id, method, params }))
    })
    if (scenario.includes('mobile')) {
      await send('Emulation.setDeviceMetricsOverride', {
        width: scenario.includes('narrow') ? 320 : 390,
        height: 844, deviceScaleFactor: 1, mobile: true
      })
    }
    await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/__order-selection-check?' + scenario })
    await send('Page.bringToFront')
    const readResult = async (reloading = false) => {
      let result
      const screenshotsTaken = new Set()
      for (let count = 0; count < 200; count++) {
        if (scenario.includes('visual')) {
          const screenshotState = await send('Runtime.evaluate', {
            expression: 'window.inlineScreenshotClip && ({ name: window.inlineScreenshotName, clip: window.inlineScreenshotClip })',
            returnByValue: true
          })
          const screenshotInfo = screenshotState.result?.value
          if (screenshotInfo && !screenshotsTaken.has(screenshotInfo.name)) {
            const screenshot = await send('Page.captureScreenshot', {
              format: 'png', captureBeyondViewport: true, clip: screenshotInfo.clip
            })
            const screenshotDirectory = join(tmpdir(), 'order-system-browser-checks')
            await mkdir(screenshotDirectory, { recursive: true })
            const screenshotPath = join(screenshotDirectory, scenario + '-' + screenshotInfo.name + '.png')
            await writeFile(screenshotPath, Buffer.from(screenshot.data, 'base64'))
            console.log('Screenshot: ' + screenshotPath)
            screenshotsTaken.add(screenshotInfo.name)
            await send('Runtime.evaluate', { expression: 'window.continueInlineTest()' })
          }
        }
        const response = await send('Runtime.evaluate', {
          expression: 'document.querySelector("#result")?.textContent',
          returnByValue: true
        })
        result = response.result?.value
        if (result && result !== 'pending') {
          const parsed = JSON.parse(result)
          if (!reloading || parsed.phase !== 'reload' || !parsed.pass) return result
        }
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      return result
    }
    let result = await readResult()
    if (result && result !== 'pending' && JSON.parse(result).pass && JSON.parse(result).phase === 'reload') {
      await send('Page.reload')
      result = await readResult(true)
      if (result && result !== 'pending' && JSON.parse(result).phase !== 'complete') process.exitCode = 1
    }
    console.log(scenario + ': ' + (result || stderr.slice(-3000)))
    if (!result || result === 'pending' || !JSON.parse(result).pass) process.exitCode = 1
    await send('Browser.close')
  } finally {
    socket?.close()
    if (child.exitCode === null) child.kill()
    await closed
  }
} finally {
  await server.close()
  if (!resolve(profile).startsWith(resolve(tmpdir()) + sep)) throw new Error('Refusing to remove a browser profile outside the temporary directory')
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
}
