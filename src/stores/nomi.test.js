import assert from 'node:assert/strict'
import test from 'node:test'
import { createPinia } from 'pinia'
import { useNomiStore } from './nomi.js'

test('switching filter tabs shows a hint before the filter form', () => {
  const nomi = useNomiStore(createPinia())

  nomi.showWelcomeMessage('hello')
  nomi.showFilterPrompt('shipped')
  assert.equal(nomi.showSpeechBubble, true)
  assert.equal(nomi.speechBubbleType, 'filter-prompt')
  assert.equal(nomi.filterType, 'shipped')

  nomi.showFilterPrompt('material')
  assert.equal(nomi.speechBubbleType, 'filter-prompt')
  assert.equal(nomi.filterType, 'material')

  nomi.showDateFilterBubble('material')
  assert.equal(nomi.showSpeechBubble, true)
  assert.equal(nomi.speechBubbleType, 'filter')
  assert.equal(nomi.filterType, 'material')

  nomi.hideSpeechBubble()
  assert.equal(nomi.showSpeechBubble, false)
})
