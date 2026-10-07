<template>
  <div class="sf-attachments">
    <div class="sf-actions">
      <strong>附件</strong>
      <button v-if="!readonly" type="button" class="sf-button" :disabled="uploading || !storeId || modelValue.length >= 10" @click="fileInput?.click()">
        <Paperclip :size="16" />{{ uploading ? '上传中...' : '添加附件' }}
      </button>
      <input v-if="!readonly" ref="fileInput" class="sf-file-input" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" :disabled="uploading || !storeId || modelValue.length >= 10" @change="upload" />
      <span v-if="!modelValue.length" class="sf-muted">暂无附件</span>
    </div>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <ul class="sf-attachment-list">
      <li v-for="(file, index) in modelValue" :key="file.url">
        <a :href="file.url" target="_blank" rel="noopener">{{ file.name }}</a>
        <button v-if="!readonly" type="button" class="sf-button icon danger" title="移除附件" aria-label="移除附件" @click="emit('update:modelValue', modelValue.filter((_, i) => i !== index))"><X :size="14" /></button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Paperclip, X } from '@lucide/vue'
import request from '@/api/request'
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  storeId: { type: [String, Number], default: '' },
  readonly: Boolean
})
const emit = defineEmits(['update:modelValue', 'uploading'])
const uploading = ref(false)
const fileInput = ref(null)
const error = ref('')
async function upload(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (file.size > 10 * 1024 * 1024) { error.value = '附件不能超过 10MB'; return }
  uploading.value = true
  emit('uploading', true)
  error.value = ''
  try {
    const body = new FormData()
    body.append('storeId', props.storeId)
    body.append('attachment', file)
    const attachment = await request.post('/supplier-finance/attachments', body, { headers: { 'Content-Type': 'multipart/form-data' } })
    emit('update:modelValue', [...props.modelValue, attachment])
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { uploading.value = false; emit('uploading', false) }
}
</script>
