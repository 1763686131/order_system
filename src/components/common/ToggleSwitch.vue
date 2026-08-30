<template>
  <div class="toggle-switch">
    <label class="switch">
      <input
        type="checkbox"
        :checked="modelValue"
        @change="$emit('update:modelValue', $event.target.checked)"
      />
      <span class="slider"></span>
    </label>
    <span v-if="showLabel" class="toggle-label">
      {{ modelValue ? activeText : inactiveText }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  showLabel: {
    type: Boolean,
    default: true
  },
  activeText: {
    type: String,
    default: '启用'
  },
  inactiveText: {
    type: String,
    default: '停用'
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.toggle-switch {
  display: flex;
  align-items: center;
  gap: 12px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #d1d5db;
  transition: 0.3s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #10b981;
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.toggle-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
  user-select: none;
}
</style>
