<template>
  <button
    type="button"
    class="gugu-launcher"
    :class="{ 'is-floating': floating }"
    :title="floating ? '固固助手工具菜单' : '打开固固助手（GuGu）'"
    :aria-label="floating ? '固固助手工具菜单' : '打开固固助手（GuGu）'"
    :aria-expanded="expanded"
    :aria-haspopup="floating ? 'menu' : 'dialog'"
  >
    <GuGuAvatar :angry="floating && angry" />
  </button>
</template>

<script setup>
import GuGuAvatar from './GuGuAvatar.vue'

defineProps({
  floating: Boolean,
  expanded: Boolean,
  angry: Boolean
})
</script>

<style scoped>
.gugu-launcher {
  position: relative;
  display: inline-flex;
  box-sizing: border-box;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  vertical-align: middle;
  transition: box-shadow 0.18s ease;
}

.gugu-launcher:hover,
.gugu-launcher[aria-expanded="true"] {
  box-shadow: 0 0 0 2px #a9e5d2;
}

.gugu-launcher:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 3px;
}

.gugu-launcher.is-floating {
  width: 70px;
  height: 70px;
  flex-basis: 70px;
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.gugu-launcher.is-floating:active {
  cursor: grabbing;
}

@media (prefers-reduced-motion: reduce) {
  .gugu-launcher {
    transition: none;
  }
}
</style>
