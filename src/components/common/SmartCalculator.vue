<template>
  <div
    v-show="visible"
    id="smartCalculator"
    :class="{ active: visible }"
    style="position: fixed; bottom: 20px; right: 20px; width: 300px; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15); z-index: 9999; transform: translateY(0); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);"
  >
    <!-- 标题栏 -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 16px; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center;">
      <div style="font-weight: bold; font-size: 16px;">🧮 计算器</div>
      <button @click="close" style="background: rgba(255,255,255,0.2); border: none; color: white; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; transition: all 0.2s;">×</button>
    </div>

    <!-- 显示区 -->
    <div style="padding: 16px; background: #f5f5f5;">
      <div id="calcHistory" style="min-height: 20px; font-size: 13px; color: #999; text-align: right; margin-bottom: 6px;">{{ history }}</div>
      <div id="calcDisplay" style="font-size: 32px; font-weight: bold; color: #333; text-align: right; min-height: 40px; word-break: break-all;">{{ display }}</div>
    </div>

    <!-- 按键区 -->
    <div style="padding: 12px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">
      <button @click="handleInput('clear')" class="calc-btn" style="background: #ff4d4f; color: white;">C</button>
      <button @click="handleInput('back')" class="calc-btn" style="background: #faad14; color: white;">←</button>
      <button @click="handleInput('/')" class="calc-btn calc-operator">÷</button>
      <button @click="handleInput('*')" class="calc-btn calc-operator">×</button>

      <button @click="handleInput('7')" class="calc-btn">7</button>
      <button @click="handleInput('8')" class="calc-btn">8</button>
      <button @click="handleInput('9')" class="calc-btn">9</button>
      <button @click="handleInput('-')" class="calc-btn calc-operator">-</button>

      <button @click="handleInput('4')" class="calc-btn">4</button>
      <button @click="handleInput('5')" class="calc-btn">5</button>
      <button @click="handleInput('6')" class="calc-btn">6</button>
      <button @click="handleInput('+')" class="calc-btn calc-operator">+</button>

      <button @click="handleInput('1')" class="calc-btn">1</button>
      <button @click="handleInput('2')" class="calc-btn">2</button>
      <button @click="handleInput('3')" class="calc-btn">3</button>
      <button @click="handleInput('=')" class="calc-btn" style="background: #52c41a; color: white; grid-row: span 2;">=</button>

      <button @click="handleInput('0')" class="calc-btn" style="grid-column: span 2;">0</button>
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
.calc-btn {
  padding: 16px;
  font-size: 18px;
  font-weight: bold;
  border: none;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}

.calc-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.12);
}

.calc-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}

.calc-operator {
  background: #e6f4ff;
  color: #1890ff;
  font-weight: bold;
}

#smartCalculator:not(.active) {
  transform: translateY(400px);
  opacity: 0;
  pointer-events: none;
}
</style>
