<template>
  <template v-if="mode === 'admin'">
    <GuGuLauncher :expanded="modelValue" @click="openChat" />
    <GuGuChat
      :model-value="modelValue"
      :open-order="openOrder"
      @update:model-value="emit('update:modelValue', $event)"
      @open-settings="emit('open-settings')"
    />
  </template>
  <GuGuTouchTools
    v-else
    @create-material="emit('create-material')"
    @date-filter="emit('date-filter', $event)"
  />
</template>

<script setup>
import GuGuChat from './GuGuChat.vue'
import GuGuLauncher from './GuGuLauncher.vue'
import GuGuTouchTools from './GuGuTouchTools.vue'

defineProps({
  mode: {
    type: String,
    required: true,
    validator: value => ['admin', 'touch'].includes(value)
  },
  modelValue: Boolean,
  openOrder: Function
})

const emit = defineEmits([
  'update:modelValue',
  'open',
  'open-settings',
  'create-material',
  'date-filter'
])

const openChat = () => {
  emit('open')
  emit('update:modelValue', true)
}
</script>
