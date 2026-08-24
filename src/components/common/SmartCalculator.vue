<template>
  <div
    v-show="visible"
    id="smartCalculator"
    :class="{ active: visible }"
  >
    <!-- 标题栏 -->
    <div class="calc-header">
      <div class="calc-title">🧮 计算器</div>
      <button @click="close" class="calc-close">×</button>
    </div>

    <!-- 显示区 -->
    <div class="calc-display-area">
      <div id="calcHistory" class="calc-history">{{ history }}</div>
      <div id="calcDisplay" class="calc-display">{{ display }}</div>
    </div>

    <!-- 按键区 -->
    <div class="calc-buttons">
      <button @click="handleInput('clear')" class="calc-btn calc-op calc-op-clear">C</button>
      <button @click="handleInput('back')" class="calc-btn calc-op">←</button>
      <button @click="handleInput('/')" class="calc-btn calc-op">÷</button>
      <button @click="handleInput('*')" class="calc-btn calc-op">×</button>

      <button @click="handleInput('7')" class="calc-btn">7</button>
      <button @click="handleInput('8')" class="calc-btn">8</button>
      <button @click="handleInput('9')" class="calc-btn">9</button>
      <button @click="handleInput('-')" class="calc-btn calc-op">-</button>

      <button @click="handleInput('4')" class="calc-btn">4</button>
      <button @click="handleInput('5')" class="calc-btn">5</button>
      <button @click="handleInput('6')" class="calc-btn">6</button>
      <button @click="handleInput('+')" class="calc-btn calc-op">+</button>

      <button @click="handleInput('1')" class="calc-btn">1</button>
      <button @click="handleInput('2')" class="calc-btn">2</button>
      <button @click="handleInput('3')" class="calc-btn">3</button>
      <button @click="handleInput('=')" class="calc-btn calc-eq">=</button>

      <button @click="handleInput('0')" class="calc-btn calc-zero">0</button>
      <button @click="handleInput('.')" class="calc-btn">.</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const visible = ref(false)
const display = ref('0')
const history = ref('')
const expression = ref('')

// 切换显示/隐藏
const toggle = () => {
  visible.value = !visible.value
  if (visible.value && expression.value === '') {
    expression.value = ''
    display.value = '0'
    history.value = ''
  }
}

// 关闭
const close = () => {
  visible.value = false
}

// 处理输入
const handleInput = (val) => {
  // 清空
  if (val === 'clear') {
    expression.value = ''
    display.value = '0'
    history.value = ''
    return
  }

  // 退格
  if (val === 'back') {
    expression.value = expression.value.slice(0, -1)
    display.value = expression.value || '0'
    return
  }

  // 等于（计算）
  if (val === '=') {
    if (!expression.value) return

    try {
      // 替换视觉符号为 JS 运算符
      let safeExpr = expression.value.replace(/×/g, '*').replace(/÷/g, '/')

      // 安全检查：仅允许数字和运算符
      if (/[^0-9+\-*\/.]/.test(safeExpr)) {
        throw new Error('Invalid')
      }

      // 执行运算
      let result = new Function('return ' + safeExpr)()
      let finalResult = Math.round(result * 10000) / 10000

      history.value = expression.value + ' ='
      expression.value = String(finalResult)
      display.value = expression.value
    } catch (e) {
      display.value = '错误'
      expression.value = ''
    }
    return
  }

  // 处理正常输入
  let showVal = val
  if (val === '*') showVal = '×'
  if (val === '/') showVal = '÷'

  // 防止最开始直接输入运算符
  if (expression.value === '' && ['+', '-', '×', '÷'].includes(showVal)) {
    return
  }

  expression.value += showVal
  display.value = expression.value
}

// 暴露方法
defineExpose({
  toggle,
  close
})

// 监听全局事件
onMounted(() => {
  window.addEventListener('toggle-calculator', () => {
    toggle()
  })
})
</script>

<style scoped>
#smartCalculator {
  position: fixed;
  right: -300px;
  top: 50%;
  transform: translateY(-50%);
  width: 280px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.25), 0 0 2px rgba(0,0,0,0.1);
  z-index: 999999;
  padding: 16px;
  transition: all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
  opacity: 0;
  visibility: hidden;
}

#smartCalculator.active {
  right: 24px;
  opacity: 1;
  visibility: visible;
}

@media (max-width: 768px) {
  #smartCalculator {
    right: auto !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) scale(0.9) !important;
    width: 85% !important;
    max-width: 320px !important;
  }
  #smartCalculator.active {
    transform: translate(-50%, -50%) scale(1) !important;
  }
}

.calc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #888;
  font-weight: bold;
}

.calc-title {
  font-size: 14px;
  color: #888;
  font-weight: bold;
}

.calc-close {
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  color: #999;
  background: none;
  border: none;
  padding: 0;
}

.calc-close:hover {
  color: #ff4d4f;
}

.calc-display-area {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  text-align: right;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.calc-history {
  min-height: 18px;
  font-size: 13px;
  color: #888;
  margin-bottom: 4px;
}

.calc-display {
  font-size: 32px;
  font-weight: bold;
  color: #333;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  overflow-x: auto;
}

.calc-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.calc-btn {
  height: 48px;
  border: none;
  border-radius: 50%;
  font-size: 18px;
  font-weight: bold;
  background: #f0f2f5;
  color: #333;
  cursor: pointer;
  transition: all 0.1s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.calc-btn:active {
  transform: scale(0.92);
  background: #e4e7ed;
}

.calc-op {
  background: #e6f7ff;
  color: #1890ff;
}

.calc-op:active {
  background: #bae0ff;
}

.calc-op-clear {
  background: #fff1f0;
  color: #ff4d4f;
}

.calc-eq {
  background: #1890ff;
  color: #fff;
  border-radius: 18px;
  grid-row: span 2;
  height: auto;
}

.calc-eq:active {
  background: #096dd9;
}

.calc-zero {
  grid-column: span 2;
}
</style>