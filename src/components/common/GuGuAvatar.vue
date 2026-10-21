<template>
  <span class="nomi-avatar" :class="{ 'is-thinking': thinking }" aria-hidden="true">
    <span class="nomi-avatar-antenna">
      <span class="nomi-avatar-antenna-dot"></span>
    </span>
    <span class="nomi-avatar-ear is-left"></span>
    <span class="nomi-avatar-ear is-right"></span>
    <span class="nomi-avatar-face">
      <span class="nomi-avatar-eye is-left"></span>
      <span class="nomi-avatar-eye is-right"></span>
      <span class="nomi-avatar-mouth"></span>
    </span>
  </span>
</template>

<script setup>
defineProps({ thinking: Boolean })
</script>

<style scoped>
.nomi-avatar {
  position: relative;
  display: inline-block;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  overflow: visible;
  vertical-align: middle;
}

.nomi-avatar-face {
  position: absolute;
  z-index: 1;
  top: 17%;
  left: 12%;
  box-sizing: border-box;
  width: 76%;
  height: 76%;
  border: 2px solid #0f9f78;
  border-radius: 6px;
  background: #0f9f78;
  box-shadow: 0 2px 7px rgba(15, 159, 120, 0.18);
  overflow: hidden;
}

.nomi-avatar-antenna {
  position: absolute;
  z-index: 0;
  top: 3%;
  left: 50%;
  width: 2px;
  height: 15%;
  background: #0f9f78;
  transform: translateX(-50%);
}

.nomi-avatar-antenna-dot {
  position: absolute;
  top: -5px;
  left: 50%;
  width: 7px;
  height: 7px;
  border: 2px solid #0f9f78;
  border-radius: 50%;
  background: #f7fffb;
  transform: translateX(-50%);
}

.nomi-avatar-ear {
  position: absolute;
  z-index: 0;
  top: 46%;
  box-sizing: border-box;
  width: 14%;
  height: 21%;
  border: 2px solid #0f9f78;
  border-radius: 4px;
  background: #f7fffb;
}

.nomi-avatar-ear.is-left {
  left: 1%;
  transform: rotate(-12deg);
}

.nomi-avatar-ear.is-right {
  right: 1%;
  transform: rotate(12deg);
}

.nomi-avatar-eye {
  position: absolute;
  top: 25%;
  width: 19%;
  height: 28%;
  border: 2px solid #ffffff;
  border-radius: 4px;
  background: #ffffff;
  box-shadow: inset 0 2px 0 #d9fff0;
  animation: nomi-avatar-blink 4s infinite;
}

.nomi-avatar-eye.is-left { left: 22%; }
.nomi-avatar-eye.is-right { right: 22%; }

.nomi-avatar-mouth {
  position: absolute;
  top: 63%;
  left: 31%;
  width: 38%;
  height: 15%;
  border-bottom: 2px solid #ffffff;
  border-radius: 0 0 3px 3px;
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
