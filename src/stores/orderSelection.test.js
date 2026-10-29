import assert from 'node:assert/strict'
import { afterEach, beforeEach, test } from 'node:test'
import { createPinia } from 'pinia'
import { useOrderSelectionStore } from './orderSelection.js'

const STORAGE_KEY = 'admin_order_list_selections'
const originalStorage = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage')
let stored

beforeEach(() => {
  stored = new Map()
  Object.defineProperty(globalThis, 'sessionStorage', {
    configurable: true,
    value: {
      getItem: key => stored.get(key) ?? null,
      setItem: (key, value) => stored.set(key, value),
      removeItem: key => stored.delete(key)
    }
  })
})

afterEach(() => {
  if (originalStorage) Object.defineProperty(globalThis, 'sessionStorage', originalStorage)
  else delete globalThis.sessionStorage
})

test('selections survive list remounts and a new application instance', () => {
  const pinia = createPinia()
  useOrderSelectionStore(pinia).setSelectedIds('finance', 7, [2, 5])
  assert.deepEqual(useOrderSelectionStore(pinia).selectedIdsFor('finance', 7), [2, 5])
  assert.deepEqual(useOrderSelectionStore(createPinia()).selectedIdsFor('finance', 7), [2, 5])
})

test('accounts and list modes have independent selections', () => {
  const store = useOrderSelectionStore(createPinia())
  store.setSelectedIds('finance', 7, [2])
  store.setSelectedIds('logistics', 7, [3])
  store.setSelectedIds('finance', 8, [4])
  assert.deepEqual(store.selectedIdsFor('finance', 7), [2])
  assert.deepEqual(store.selectedIdsFor('logistics', 7), [3])
  assert.deepEqual(store.selectedIdsFor('finance', 8), [4])
  assert.deepEqual(store.selectedIdsFor('finance', 9), [])
})

test('clearing a selection preserves the other lists and removes the final cache', () => {
  const store = useOrderSelectionStore(createPinia())
  store.setSelectedIds('finance', 7, [2])
  store.setSelectedIds('logistics', 7, [3])
  store.setSelectedIds('finance', 7, [])
  assert.deepEqual(useOrderSelectionStore(createPinia()).selectedIdsFor('finance', 7), [])
  assert.deepEqual(useOrderSelectionStore(createPinia()).selectedIdsFor('logistics', 7), [3])
  store.setSelectedIds('logistics', 7, [])
  assert.equal(stored.has(STORAGE_KEY), false)
})

test('saved selections reject duplicates and invalid order IDs', () => {
  stored.set(STORAGE_KEY, JSON.stringify({
    '7:finance': [2, 2, -1, 0, null, '3', 1.5, 5],
    '7:logistics': 'invalid'
  }))
  const store = useOrderSelectionStore(createPinia())
  assert.deepEqual(store.selectedIdsFor('finance', 7), [2, 5])
  assert.deepEqual(store.selectedIdsFor('logistics', 7), [])
})

test('malformed storage does not prevent opening the order list', () => {
  for (const value of ['invalid JSON', 'null', '[]', '"invalid"']) {
    stored.set(STORAGE_KEY, value)
    assert.deepEqual(useOrderSelectionStore(createPinia()).selectedIdsFor('finance', 7), [])
  }
})

test('selection stays usable when browser storage throws', () => {
  Object.defineProperty(globalThis, 'sessionStorage', {
    configurable: true,
    get() { throw new Error('Storage is unavailable') }
  })
  const store = useOrderSelectionStore(createPinia())
  store.setSelectedIds('finance', 7, [2])
  assert.deepEqual(store.selectedIdsFor('finance', 7), [2])
  store.setSelectedIds('finance', 7, [])
  assert.deepEqual(store.selectedIdsFor('finance', 7), [])
})

test('selection works without browser storage', () => {
  delete globalThis.sessionStorage
  const store = useOrderSelectionStore(createPinia())
  store.setSelectedIds('finance', 7, [2])
  assert.deepEqual(store.selectedIdsFor('finance', 7), [2])
})
