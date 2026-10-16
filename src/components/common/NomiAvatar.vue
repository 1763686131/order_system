<template>
  <span class="nomi-avatar" :class="{ 'is-thinking': thinking }" aria-hidden="true">
    <span class="nomi-avatar-eye is-left"></span>
    <span class="nomi-avatar-eye is-right"></span>
    <span class="nomi-avatar-mouth"></span>
  </span>
</template>

<script setup>
defineProps({ thinking: Boolean })
</script>

<style scoped>
.nomi-avatar {
  position: relative;
  display: inline-block;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #2a3b5c, #0f172a);
  box-shadow: inset -2px -2px 5px #0009, inset 1px 1px 4px #fff3;
  vertical-align: middle;
}

.nomi-avatar-eye {
  position: absolute;
  top: 31%;
  width: 14%;
  height: 20%;
  border-radius: 6px;
  background: #00e5ff;
  animation: nomi-avatar-blink 4s infinite;
}

.nomi-avatar-eye.is-left { left: 26%; }
.nomi-avatar-eye.is-right { right: 26%; }

.nomi-avatar-mouth {
  position: absolute;
  top: 60%;
  left: 34%;
  width: 32%;
  height: 15%;
  border: 2px solid #00e5ff;
  border-top: 0;
  border-radius: 0 0 20px 20px;
}

.nomi-avatar.is-thinking .nomi-avatar-eye {
  animation: nomi-avatar-blink 1.2s infinite;
}

@keyframes nomi-avatar-blink {
  0%, 94%, 98%, 100% { transform: scaleY(1); }
  96% { transform: scaleY(0.15); }
}

@media (prefers-reduced-motion: reduce) {
  .nomi-avatar-eye,
  .nomi-avatar.is-thinking .nomi-avatar-eye {
    animation: none;
  }
}
</style>
