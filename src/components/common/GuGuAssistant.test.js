import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { after, before, test } from 'node:test'
import { baseParse, NodeTypes, parserOptions } from '@vue/compiler-dom'
import { parse } from '@vue/compiler-sfc'
import { renderToString } from '@vue/server-renderer'
import { createPinia } from 'pinia'
import { createSSRApp, h } from 'vue'
import { createServer } from 'vite'

let server
let GuGuAssistant
let GuGuTouchTools
let useNomiStore
let useUserStore
const originalWindow = globalThis.window

before(async () => {
  globalThis.window = {
    innerWidth: 390,
    innerHeight: 844,
    localStorage: { getItem: () => null }
  }
  server = await createServer({ server: { middlewareMode: true, hmr: false, ws: false } })
  ;({ default: GuGuAssistant } = await server.ssrLoadModule('/src/components/common/GuGuAssistant.vue'))
  ;({ default: GuGuTouchTools } = await server.ssrLoadModule('/src/components/common/GuGuTouchTools.vue'))
  ;({ useNomiStore } = await server.ssrLoadModule('/src/stores/nomi.js'))
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
const attribute = (node, name) => node.props.find(prop => prop.name === name)?.value?.content
const byClass = (node, name) => elements(node, element => attribute(element, 'class')?.split(/\s+/).includes(name))
const text = node => node.type === NodeTypes.TEXT ? node.content : (node.children || []).map(text).join('')
const buttons = node => elements(node, element => element.tag === 'button').map(button => text(button).trim())

const render = async ({ mode = 'touch', tab = 0, permissions = [], bubble, open = false } = {}) => {
  const pinia = createPinia()
  useUserStore(pinia).$patch({ permissions })
  const nomi = useNomiStore(pinia)
  nomi.currentTab = tab
  nomi.isMenuActive = true
  if (bubble === 'prompt') nomi.showFilterPrompt(tab === 3 ? 'material' : 'shipped')
  if (bubble === 'filter') nomi.showDateFilterBubble(tab === 3 ? 'material' : 'shipped')
  const context = {}
  const app = createSSRApp({ render: () => h(GuGuAssistant, {
    mode,
    modelValue: open,
    openOrder: async () => {}
  }) })
  app.use(pinia)
  try {
    const tree = baseParse(await renderToString(app, context), parserOptions)
    return { tree, dialog: baseParse(context.teleports?.body || '', parserOptions) }
  } finally {
    nomi.hideSpeechBubble()
  }
}

const setupTools = async () => {
  const pinia = createPinia()
  const events = []
  let tools
  const component = {
    ...GuGuTouchTools,
    setup(props, context) {
      tools = GuGuTouchTools.setup(props, context)
      return tools
    }
  }
  const app = createSSRApp({ render: () => h(component, {
    onDateFilter: payload => events.push(['filter', payload]),
    onCreateMaterial: () => events.push(['material'])
  }) })
  app.use(pinia)
  await renderToString(app)
  return { tools, events, nomi: useNomiStore(pinia) }
}

test('both modes use the same robot face and launcher without a legacy circular shell', async () => {
  const admin = (await render({ mode: 'admin' })).tree
  const touch = (await render()).tree
  for (const tree of [admin, touch]) {
    assert.equal(byClass(tree, 'gugu-launcher').length, 1)
    assert.equal(byClass(tree, 'nomi-avatar').length, 1)
    assert.equal(byClass(tree, 'nomi-avatar-face').length, 1)
    assert.equal(byClass(tree, 'ai-face').length, 0)
    assert.equal(byClass(tree, 'robot-head').length, 0)
  }
  assert.equal(byClass(admin, 'is-floating').length, 0)
  assert.equal(byClass(touch, 'is-floating').length, 1)
})

test('admin mode owns the chat dialog and does not render touch tools', async () => {
  const { tree, dialog } = await render({ mode: 'admin', open: true })
  const [launcher] = byClass(tree, 'gugu-launcher')
  assert.equal(attribute(launcher, 'aria-haspopup'), 'dialog')
  assert.equal(attribute(launcher, 'aria-expanded'), 'true')
  assert.equal(byClass(tree, 'gugu-touch-tools').length, 0)
  assert.equal(byClass(dialog, 'nomi-admin-dialog').length, 1)
  assert.equal(byClass(dialog, 'nomi-avatar').length, 1)
})

test('the shared admin entry forwards open and model updates to its host page', async () => {
  const events = []
  let assistant
  const component = {
    ...GuGuAssistant,
    setup(props, context) {
      assistant = GuGuAssistant.setup(props, context)
      return assistant
    }
  }
  const app = createSSRApp({ render: () => h(component, {
    mode: 'admin',
    openOrder: async () => {},
    onOpen: () => events.push(['open']),
    'onUpdate:modelValue': value => events.push(['model', value])
  }) })
  app.use(createPinia())
  await renderToString(app)
  assistant.openChat()
  assert.deepEqual(events, [['open'], ['model', true]])
})

test('pending and completed tabs do not expose date filters or material entry', async () => {
  for (const tab of [0, 1]) {
    const { tree, dialog } = await render({ tab, permissions: ['touch.material.create'] })
    assert.deepEqual(buttons(byClass(tree, 'gugu-touch-menu')[0]), ['退出登录'])
    assert.equal(byClass(dialog, 'nomi-admin-dialog').length, 0)
  }
})

test('logistics filtering and permission-gated material entry remain separated by tab', async () => {
  const logistics = await render({ tab: 2, permissions: ['touch.material.create'] })
  assert.deepEqual(buttons(byClass(logistics.tree, 'gugu-touch-menu')[0]), ['筛选', '退出登录'])
  const restricted = await render({ tab: 3 })
  assert.deepEqual(buttons(byClass(restricted.tree, 'gugu-touch-menu')[0]), ['筛选', '退出登录'])
  const allowed = await render({ tab: 3, permissions: ['touch.material.create'] })
  assert.deepEqual(buttons(byClass(allowed.tree, 'gugu-touch-menu')[0]), ['录入原材料出库', '筛选', '退出登录'])
})

test('touch mode keeps the filter prompt and accessible date form', async () => {
  const prompt = await render({ tab: 2, bubble: 'prompt' })
  assert.equal(byClass(prompt.tree, 'gugu-filter-link').length, 1)
  for (const tab of [2, 3]) {
    const { tree } = await render({ tab, bubble: 'filter' })
    const [form] = byClass(tree, 'gugu-filter-form')
    assert.equal(elements(form, element => element.tag === 'input' && attribute(element, 'type') === 'date').length, 2)
    assert.deepEqual(buttons(form), ['最近一周', '恢复默认', '开始筛选'])
    assert.ok(text(form).includes(tab === 3 ? '原材料日期范围' : '物流订单日期范围'))
  }
})

test('touch filter and material actions preserve their event payloads', async () => {
  const { tools, events, nomi } = await setupTools()
  nomi.currentTab = 3
  try {
    tools.openDateFilter()
    assert.equal(nomi.filterType, 'material')
    tools.filterStartDate.value = '2026-10-01'
    tools.filterEndDate.value = '2026-10-21'
    tools.handleConfirmFilter()
    tools.handleResetFilter()
    tools.handleCreateMaterial()
    assert.deepEqual(events, [
      ['filter', { type: 'material', startDate: '2026-10-01', endDate: '2026-10-21' }],
      ['filter', { type: 'material', startDate: '', endDate: '' }],
      ['material']
    ])
    assert.equal(nomi.showSpeechBubble, false)
  } finally {
    nomi.hideSpeechBubble()
  }
})

test('touch dragging stays on screen and does not open the menu when released', async () => {
  const { tools, nomi } = await setupTools()
  let captured = false
  const handle = {
    setPointerCapture: () => { captured = true },
    hasPointerCapture: () => captured,
    releasePointerCapture: () => { captured = false }
  }
  tools.fabContainer.value = {
    offsetWidth: 70,
    offsetHeight: 70,
    getBoundingClientRect: () => ({ left: 200, top: 500 })
  }
  tools.handleDragStart({
    isPrimary: true, button: 0, pointerId: 1,
    currentTarget: handle, clientX: 200, clientY: 500
  })
  tools.handleDrag({ pointerId: 1, clientX: 2000, clientY: 2000, preventDefault() {} })
  assert.deepEqual(tools.position.value, { x: 320, y: 774 })
  tools.handleDragEnd({ pointerId: 1 })
  tools.handleClick({ detail: 1 })
  assert.equal(captured, false)
  assert.equal(nomi.isMenuActive, false)
  tools.handleClick({ detail: 0 })
  assert.equal(nomi.isMenuActive, true)
})

test('touch popovers stay within a narrow viewport when the robot is at an edge', async () => {
  const originalDocument = globalThis.document
  globalThis.document = { documentElement: { clientWidth: 390, clientHeight: 844 } }
  try {
    const { tools } = await setupTools()
    tools.fabContainer.value = {
      getBoundingClientRect: () => ({ left: 320, right: 390, top: 0, bottom: 70, height: 70 })
    }
    tools.menuRef.value = { getBoundingClientRect: () => ({ width: 210, height: 160 }) }
    tools.speechBubble.value = { getBoundingClientRect: () => ({ width: 366, height: 180 }) }
    await tools.updatePopoverPositions()
    assert.deepEqual(tools.menuPosition.value, { left: '168px', top: '82px' })
    assert.deepEqual(tools.bubblePosition.value, { left: '12px', top: '12px' })
  } finally {
    if (originalDocument === undefined) delete globalThis.document
    else globalThis.document = originalDocument
  }
})

test('robot styling is component-scoped and absent from global styles', async () => {
  for (const name of ['GuGuAvatar', 'GuGuLauncher', 'GuGuChat', 'GuGuOrderDraft', 'GuGuTouchTools']) {
    const source = await readFile(new URL(`./${name}.vue`, import.meta.url), 'utf8')
    const { descriptor } = parse(source)
    assert.ok(descriptor.styles.length > 0)
    assert.ok(descriptor.styles.every(style => style.scoped))
  }
  const globalStyles = await readFile(new URL('../../assets/styles/main.css', import.meta.url), 'utf8')
  const searchStyles = await readFile(new URL('../../assets/styles/original-search.css', import.meta.url), 'utf8')
  assert.ok(!globalStyles.includes('original-nomi'))
  assert.ok(!/\.ai-face|\.robot-head|\.fab-container|\.nomi-avatar/.test(searchStyles))
})
