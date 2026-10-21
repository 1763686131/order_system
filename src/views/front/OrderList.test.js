import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { baseParse, NodeTypes } from '@vue/compiler-dom'
import { renderToString } from '@vue/server-renderer'
import { createPinia } from 'pinia'
import { createSSRApp, h } from 'vue'
import { createServer } from 'vite'

let server
let OrderList
let useUserStore
const originalWindow = globalThis.window
const order = {
  id: 42,
  order_client: 'Test client',
  date: '2026-10-20 09:00:00',
  completed_date: '2026-10-21 10:00:00',
  contact_person: 'Test receiver',
  contact_phone: '13800000000',
  contact_address: 'Test address',
  order_goods: [{ goods_name: 'Product', spec: 'A100', quantity: 20, unit: 'kg', packages: 2 }]
}

before(async () => {
  globalThis.window = { innerWidth: 1920 }
  server = await createServer({ server: { middlewareMode: true, hmr: false } })
  ;({ default: OrderList } = await server.ssrLoadModule('/src/views/front/OrderList.vue'))
  ;({ useUserStore } = await server.ssrLoadModule('/src/stores/user.js'))
})

after(async () => {
  await server?.close()
  if (originalWindow === undefined) delete globalThis.window
  else globalThis.window = originalWindow
})

const elements = (node, predicate) => {
  const matches = node.type === NodeTypes.ELEMENT && predicate(node) ? [node] : []
  return matches.concat((node.children || []).flatMap(child => elements(child, predicate)))
}

const byClass = (node, className) => elements(node, element => element.props.some(prop => (
  prop.name === 'class' && prop.value?.content.split(/\s+/).includes(className)
)))
const text = node => node.type === NodeTypes.TEXT
  ? node.content
  : (node.children || []).map(text).join('')
const buttons = node => elements(node, element => element.tag === 'button').map(node => text(node).trim())

const render = async (statusType, { goods = order.order_goods, permissions, width = 1920 } = {}) => {
  globalThis.window.innerWidth = width
  const pinia = createPinia()
  useUserStore(pinia).$patch({
    isSuperAdmin: permissions === undefined,
    canAccessAdmin: permissions === undefined,
    permissions: permissions || []
  })
  const app = createSSRApp({ render: () => h(OrderList, {
    orders: [{ ...order, order_goods: goods }],
    statusType
  }) })
  app.use(pinia)
  return baseParse(await renderToString(app))
}

test('completed cards default to the shared minimal front with their action menu', async () => {
  const tree = await render('completed')
  const [front] = byClass(tree, 'front')
  const [back] = byClass(tree, 'back')

  assert.equal(byClass(tree, 'flip-container').length, 1)
  assert.equal(byClass(tree, 'flipped').length, 0)
  assert.equal(byClass(tree, 'completed-card').length, 0)
  assert.equal(byClass(front, 'product-info-box').length, 1)
  assert.equal(byClass(front, 'goods-packages').length, 1)
  assert.equal(byClass(front, 'tags-wrapper').length, 1)
  assert.deepEqual(buttons(front), ['撤销已完成', '删除', '复制', '详情页面'])
  assert.ok(!text(front).includes(order.contact_address))
  assert.ok(text(back).includes(order.contact_address))
  assert.ok(text(back).includes(order.completed_date))
  assert.deepEqual(buttons(back), ['⇦返回', '撤销已完成', '删除', '复制'])
})

test('pending cards keep their existing front and back actions', async () => {
  const tree = await render('pending')
  assert.deepEqual(buttons(byClass(tree, 'front')[0]), ['确定完成', '详情页面'])
  assert.deepEqual(buttons(byClass(tree, 'back')[0]), ['⇦返回', '确定完成', '复制'])
  assert.ok(!text(byClass(tree, 'back')[0]).includes('完成时间'))
})

test('only completed cards show a stamp beside each front and back title, including continuation cards', async () => {
  const goods = Array.from({ length: 5 }, () => ({ ...order.order_goods[0] }))
  for (const statusType of ['pending', 'completed']) {
    const tree = await render(statusType, { goods })
    const cards = byClass(tree, 'order-card')
    assert.equal(cards.length, 3)
    for (const card of cards) {
      const [title] = byClass(card, 'order-title')
      const stamps = byClass(title, 'completed-stamp')
      assert.equal(stamps.length, statusType === 'completed' ? 1 : 0)
      if (stamps.length) assert.equal(text(stamps[0]), '已完成')
    }
  }
})

test('completed card actions and private details still respect permissions', async () => {
  const tree = await render('completed', { permissions: ['touch.order.read'] })
  assert.deepEqual(buttons(byClass(tree, 'front')[0]), ['详情页面'])
  assert.deepEqual(buttons(byClass(tree, 'back')[0]), ['⇦返回'])
  assert.ok(!text(tree).includes(order.contact_phone))
})

test('completed and pending cards use the same package-aware desktop splitting', async () => {
  const goods = Array.from({ length: 5 }, (_, index) => ({
    ...order.order_goods[0], goods_name: `Product ${index}`
  }))
  for (const statusType of ['pending', 'completed']) {
    const tree = await render(statusType, { goods })
    const fronts = byClass(tree, 'front')
    assert.equal(fronts.length, 2)
    assert.deepEqual(fronts.map(front => byClass(front, 'product-row').length), [4, 1])
    assert.equal(byClass(tree, 'back').length, 1)
    assert.equal(byClass(tree, 'no-flip').length, 1)
    assert.equal(buttons(fronts[1]).length, 0)
  }
})

test('mobile completed orders keep all goods together on a single minimal card', async () => {
  const goods = Array.from({ length: 10 }, () => ({ ...order.order_goods[0] }))
  const tree = await render('completed', { goods, width: 390 })
  assert.equal(byClass(tree, 'front').length, 1)
  assert.equal(byClass(byClass(tree, 'front')[0], 'product-row').length, 10)
  assert.equal(byClass(byClass(tree, 'front')[0], 'completed-stamp').length, 1)
})
