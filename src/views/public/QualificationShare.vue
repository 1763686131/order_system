<template>
  <main class="public-qualification">
    <div v-if="loading" class="page-state" role="status">正在加载...</div>
    <section v-else-if="error" class="page-state" role="alert">
      <h1>{{ unavailable ? '分享已关闭或链接无效' : '暂时无法加载' }}</h1>
      <button v-if="!unavailable" type="button" @click="loadDocument">重新加载</button>
    </section>
    <QualificationDetails v-else-if="documentData" :title="documentData.title" :fields="documentData.fields" />
  </main>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import QualificationDetails from '@/components/qualifications/QualificationDetails.vue'

const props = defineProps({ token: { type: String, required: true } })
const documentData = ref(null)
const loading = ref(true)
const error = ref(false)
const unavailable = ref(false)
const originalTitle = document.title
let controller
let refreshTimer
let disposed = false

async function loadDocument() {
  controller?.abort()
  const activeController = new AbortController()
  controller = activeController
  error.value = false
  unavailable.value = false
  if (!documentData.value) loading.value = true
  try {
    if (!/^[A-Za-z0-9_-]{43}$/.test(props.token)) {
      unavailable.value = true
      throw new Error('Invalid share link')
    }
    const response = await fetch(`/api/hr/qualifications/share/${encodeURIComponent(props.token)}`, {
      credentials: 'omit',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      signal: activeController.signal
    })
    if (activeController !== controller || disposed) return
    unavailable.value = response.status === 404 || response.status === 410
    if (!response.ok) throw new Error('Shared document unavailable')
    const data = await response.json()
    if (!data.success) throw new Error('Shared document unavailable')
    if (activeController !== controller || disposed) return
    documentData.value = data.data
    document.title = data.data.title
  } catch (failure) {
    if (failure.name === 'AbortError' || activeController !== controller || disposed) return
    documentData.value = null
    error.value = true
    document.title = unavailable.value ? '分享已关闭或链接无效' : '暂时无法加载'
  } finally {
    if (activeController === controller && !disposed) loading.value = false
  }
}

function refreshWhenVisible() {
  if (!document.hidden) loadDocument()
}

watch(() => props.token, () => {
  documentData.value = null
  loadDocument()
}, { immediate: true })

onMounted(() => {
  // Recheck revocation when a customer returns to the tab or keeps it open.
  document.addEventListener('visibilitychange', refreshWhenVisible)
  window.addEventListener('pageshow', refreshWhenVisible)
  refreshTimer = window.setInterval(refreshWhenVisible, 30000)
})

onBeforeUnmount(() => {
  disposed = true
  controller?.abort()
  window.clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', refreshWhenVisible)
  window.removeEventListener('pageshow', refreshWhenVisible)
  document.title = originalTitle
})
</script>

<style scoped>
.public-qualification {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 100dvh;
  padding: 32px 20px;
  background: #f5f7f9;
  box-sizing: border-box;
}
.page-state {
  width: 100%;
  max-width: 760px;
  padding: 60px 16px;
  color: #6b7280;
  text-align: center;
}
.page-state h1 { margin: 0; font-size: 18px; font-weight: 500; }
.page-state button {
  margin-top: 20px;
  padding: 9px 18px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #2563eb;
  font: inherit;
  cursor: pointer;
}
@media (max-width: 600px) {
  .public-qualification { padding: 16px 12px; }
}
</style>
