<template>
  <Teleport to="body" :disabled="embedded">
    <div :class="embedded ? 'sf-embedded-layer' : 'sf-modal-layer'" @click.self="close">
      <section
        ref="documentElement"
        class="supplier-finance-dialog"
        :class="{ 'sf-embedded-document': embedded }"
        :role="embedded ? 'region' : 'dialog'"
        :aria-modal="embedded ? undefined : true"
        :aria-label="ariaLabel || title"
      >
        <header class="sf-header">
          <h2>{{ title }} <slot name="title-extra" /></h2>
          <button v-if="!embedded" type="button" class="sf-button icon" title="关闭" aria-label="关闭" :disabled="busy" @click="close">
            <X :size="18" />
          </button>
        </header>
        <div class="sf-dialog-body">
          <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
          <p v-if="loading" class="sf-empty">加载单据中...</p>
          <form v-else-if="!loadFailed" :id="formId" @submit.prevent="submit">
            <slot />
          </form>
        </div>
        <footer class="sf-footer">
          <button class="sf-button" type="button" :disabled="busy" @click="close">
            <ArrowLeft v-if="embedded" :size="16" />{{ closeLabel || (embedded ? '返回' : '关闭') }}
          </button>
          <div class="sf-actions"><slot name="actions" /></div>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { ArrowLeft, X } from '@lucide/vue'
import '@/assets/styles/supplier-finance.css'

const props = defineProps({
  title: { type: String, required: true },
  formId: { type: String, required: true },
  ariaLabel: { type: String, default: '' },
  closeLabel: { type: String, default: '' },
  error: { type: String, default: '' },
  embedded: Boolean,
  busy: Boolean,
  loading: Boolean,
  loadFailed: Boolean
})
const emit = defineEmits(['close', 'submit'])
const documentElement = ref(null)

function close() {
  if (!props.busy) emit('close')
}

function submit() {
  if (!props.busy && !props.loading && !props.loadFailed) emit('submit')
}

defineExpose({
  scrollIntoView: options => documentElement.value?.scrollIntoView(options),
  focusField: selector => documentElement.value?.querySelector(selector)?.focus({ preventScroll: true })
})
</script>
