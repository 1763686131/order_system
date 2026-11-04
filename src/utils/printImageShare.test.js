import assert from 'node:assert/strict'
import test from 'node:test'
import { effectScope, ref } from 'vue'
import { usePrintImageShare } from '../composables/usePrintImageShare.js'
import { getPrintImageAction } from './printImageShare.js'

const iphone = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)'
const png = new Blob(['test-image'], { type: 'image/png' })

function deferred() {
  let resolve
  let reject
  const promise = new Promise((accept, fail) => { resolve = accept; reject = fail })
  return { promise, resolve, reject }
}

function fixture(t, { userAgent = iphone, navigator = {}, capture = async () => png } = {}) {
  const created = []
  const revoked = []
  const calls = []
  const environment = {
    File,
    FileReader: class {
      readAsDataURL(blob) {
        blob.arrayBuffer().then(bytes => {
          this.result = `data:${blob.type};base64,${Buffer.from(bytes).toString('base64')}`
          this.onload()
        })
      }
    },
    URL: {
      createObjectURL(file) {
        const url = `blob:print-test/${created.length + 1}`
        created.push({ url, file })
        return url
      },
      revokeObjectURL(url) { revoked.push(url) }
    },
    navigator: {
      userAgent,
      canShare: () => true,
      share(data) { calls.push(data); return Promise.resolve() },
      ...navigator
    }
  }
  const scope = effectScope()
  const fileName = ref('order-001.png')
  const state = scope.run(() => usePrintImageShare({ environment, capture, fileName }))
  t.after(() => scope.stop())
  return { state, environment, created, revoked, calls, scope, fileName }
}

test('WeChat on iOS and Android opens a PNG without invoking native sharing', async t => {
  for (const userAgent of [iphone + ' MicroMessenger/8', 'Mozilla/5.0 (Linux; Android 14) MicroMessenger/8']) {
    const { state, calls, created } = fixture(t, { userAgent })
    await state.prepare({})
    assert.equal(state.action.value, 'preview')
    assert.equal(state.unavailableReason.value, '')
    assert.equal(state.canSystemShare.value, false)
    await state.share()
    assert.equal(state.previewVisible.value, true)
    assert.match(state.previewImageUrl.value, /^data:image\/png;base64,/)
    assert.equal(state.downloadUrl.value, created[0].url)
    assert.equal(created[0].file.name, 'order-001.png')
    assert.equal(await created[0].file.text(), 'test-image')
    assert.equal(calls.length, 0)
    assert.equal(state.error.value, '')
    state.closePreview()
    assert.equal(state.previewVisible.value, false)
    assert.equal(state.ready.value, true)
  }
})

test('missing, unsupported or failing file-share capability uses the mobile preview', async t => {
  for (const navigator of [
    { share: undefined },
    { canShare: () => false },
    { canShare() { throw new Error('Unsupported capability check') } }
  ]) {
    const { state, calls } = fixture(t, { navigator })
    await state.prepare({})
    await state.share()
    assert.equal(state.previewVisible.value, true)
    assert.equal(state.error.value, '')
    assert.equal(calls.length, 0)
  }
})

test('native file sharing is invoked synchronously with the generated file', async t => {
  const pending = deferred()
  let duringTap = false
  const { state, calls } = fixture(t, {
    navigator: { share(data) {
      assert.equal(duringTap, true)
      calls.push(data)
      return pending.promise
    } }
  })
  await state.prepare({})
  assert.equal(state.canSystemShare.value, true)
  duringTap = true
  const sharing = state.share()
  duringTap = false
  assert.equal(calls.length, 1)
  assert.equal(state.sharing.value, true)
  assert.deepEqual(Object.keys(calls[0]), ['files'])
  assert.equal(calls[0].files[0].name, 'order-001.png')
  assert.equal(calls[0].files[0].type, 'image/png')
  pending.resolve()
  await sharing
  assert.equal(state.previewVisible.value, false)
  assert.equal(state.message.value, '已交给系统分享。')
})

test('native permission failures and other errors retain the image for preview and retry', async t => {
  for (const name of ['NotAllowedError', 'SecurityError', 'TypeError']) {
    let fail = true
    const { state } = fixture(t, {
      navigator: { share() {
        if (fail) throw new DOMException('Sharing failed', name)
        return Promise.resolve()
      } }
    })
    await state.prepare({})
    const url = state.previewImageUrl.value
    await state.share()
    assert.equal(state.previewVisible.value, true)
    assert.equal(state.previewImageUrl.value, url)
    assert.equal(state.error.value, '')
    assert.equal(state.previewNotice.value, '系统分享暂时不可用')
    fail = false
    await state.share()
    assert.equal(state.previewVisible.value, false)
    assert.equal(state.previewNotice.value, '')
  }
})

test('cancelling native sharing does not open the fallback or report success', async t => {
  const { state } = fixture(t, {
    navigator: { share: () => Promise.reject(new DOMException('Cancelled', 'AbortError')) }
  })
  await state.prepare({})
  await state.share()
  assert.equal(state.previewVisible.value, false)
  assert.equal(state.error.value, '')
  assert.equal(state.message.value, '')
  assert.equal(state.ready.value, true)
})

test('changing a document closes the preview and replaces its image and filename', async t => {
  const { state, revoked, created, fileName, scope } = fixture(t, {
    userAgent: iphone + ' MicroMessenger'
  })
  await state.prepare({})
  await state.share()
  fileName.value = 'order-002.png'
  const preparing = state.prepare({})
  assert.equal(state.previewVisible.value, false)
  assert.equal(state.previewImageUrl.value, '')
  assert.equal(state.downloadUrl.value, '')
  assert.deepEqual(revoked, [created[0].url])
  await preparing
  await state.share()
  assert.equal(state.imageName.value, 'order-002.png')
  scope.stop()
  assert.equal(state.previewVisible.value, false)
  assert.equal(state.previewImageUrl.value, '')
  assert.deepEqual(revoked, created.map(item => item.url))
})

test('obsolete captures and pending native shares cannot reopen an old document', async t => {
  const capture = deferred()
  const { state, created } = fixture(t, { capture: () => capture.promise })
  const preparing = state.prepare({})
  state.invalidate()
  capture.resolve(png)
  await preparing
  assert.equal(created.length, 0)
  assert.equal(state.ready.value, false)

  const pending = deferred()
  const next = fixture(t, { navigator: { share: () => pending.promise } })
  await next.state.prepare({})
  const sharing = next.state.share()
  next.state.invalidate()
  pending.reject(new Error('Old share failed'))
  await sharing
  assert.equal(next.state.previewVisible.value, false)
  assert.equal(next.state.message.value, '')
  assert.equal(next.state.error.value, '')
})

test('mobile previews can use a Blob URL when data URL reading is unavailable', async t => {
  const { state, environment, created } = fixture(t, { userAgent: iphone + ' MicroMessenger' })
  environment.FileReader = undefined
  await state.prepare({})
  await state.share()
  assert.equal(state.previewVisible.value, true)
  assert.equal(state.previewImageUrl.value, created[0].url)
})

test('desktop still copies the PNG to the clipboard without a preview or object URL', async t => {
  let copied
  const { state, environment, created } = fixture(t, {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    navigator: { clipboard: { write(items) { copied = items; return Promise.resolve() } } }
  })
  environment.ClipboardItem = class {
    constructor(data) { this.data = data }
  }
  assert.equal(getPrintImageAction(null, environment), 'copy')
  await state.prepare({})
  await state.share()
  assert.equal(copied.length, 1)
  assert.equal(copied[0].data['image/png'].name, 'order-001.png')
  assert.equal(await copied[0].data['image/png'].text(), 'test-image')
  assert.equal(state.message.value, '单据图片已复制，可直接粘贴发送。')
  assert.equal(state.previewVisible.value, false)
  assert.equal(created.length, 0)
})
