<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="uploadMaterialModal"
      class="old-modal-mask"
    >
      <div class="old-modal-box" style="max-width: 760px;">
        <div class="old-modal-header">
          <span style="color:#1890ff; font-weight:bold;">原材料数据录入</span>
          <span class="old-close-x" @click="handleClose">&times;</span>
        </div>

        <div class="old-modal-body upload-modal-body" style="padding: 24px; display: flex; gap: 32px;">
          <!-- 左侧输入区 -->
          <div class="upload-inputs-area" style="flex: 1.2; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div class="form-item" style="margin-bottom: 20px;">
                <label for="materialInputUse" style="font-weight:bold; color:#ff4d4f; margin-bottom: 8px; display: block;">今日消耗原材料 (kg):</label>
                <input
                  v-model="usedValue"
                  id="materialInputUse"
                  readonly
                  placeholder="点击右侧键盘输入..."
                  class="keyboard-target"
                  :class="{ 'active-target': activeTarget === 'used' }"
                  @click="setActiveTarget('used')"
                  style="background:#f9fafc; font-size:18px; font-weight:bold; padding: 12px 16px; border: 1px solid #e4e7ed; border-radius: 8px; width: 100%; box-sizing: border-box; outline: none;"
                />
              </div>

              <div class="form-item" style="margin-bottom: 20px;">
                <label for="materialInputProduct" style="font-weight:bold; color:#52c41a; margin-bottom: 8px; display: block;">出货成品总数量 (kg):</label>
                <input
                  v-model="producedValue"
                  id="materialInputProduct"
                  readonly
                  placeholder="点击右侧键盘输入..."
                  class="keyboard-target"
                  :class="{ 'active-target': activeTarget === 'produced' }"
                  @click="setActiveTarget('produced')"
                  style="background:#f9fafc; font-size:18px; font-weight:bold; padding: 12px 16px; border: 1px solid #e4e7ed; border-radius: 8px; width: 100%; box-sizing: border-box; outline: none;"
                />
              </div>
            </div>

            <div class="form-item" style="margin-top: auto; padding-top: 10px; border-top: 1px dashed #eee;">
              <label for="materialInputRemark" style="font-weight:bold; color:#1890ff; display: block; margin-bottom: 8px;">附加备注信息 (选填):</label>
              <input
                v-model="remarkValue"
                id="materialInputRemark"
                placeholder="可手动打字，或直接点击下方快捷标签"
                style="background:#fff; font-size:14px; border: 1px solid #d9d9d9; border-radius: 6px; padding: 10px 12px; width: 100%; box-sizing: border-box; outline: none; color: #333;"
              />
              <div id="materialRemarkTags" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; min-height: 24px; align-items: center;">
                <span
                  v-for="tag in remarkTags"
                  :key="tag"
                  @click="remarkValue = tag"
                  style="cursor: pointer; background: #e6f4ff; color: #1677ff; border: 1px solid #91caff; padding: 4px 10px; border-radius: 4px; font-size: 12px; transition: all 0.2s; user-select: none;"
                  @mouseover="$event.target.style.background='#bae0ff'"
                  @mouseout="$event.target.style.background='#e6f4ff'"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>

          <!-- 右侧键盘区 -->
          <div class="upload-keyboard-area" style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
            <div class="touch-keyboard-panel" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px;">
              <button class="key-btn" v-for="n in 9" :key="n" @click="pressKey(n.toString())">{{ n }}</button>
              <button class="key-btn" @click="pressKey('.')">.</button>
              <button class="key-btn" @click="pressKey('0')">0</button>
              <button class="key-btn key-backspace" @click="pressKey('backspace')">←</button>
              <button class="key-btn key-clear" @click="pressKey('clear')" style="grid-column: span 3; font-size:15px; height: 42px; background:#f0f2f5; color:#555; font-weight: bold;">清空重输</button>
            </div>

            <div class="old-modal-footer" style="padding: 0; border: none; display: flex; gap: 12px; justify-content: center; background: transparent;">
              <button class="btn-default" @click="handleClose" style="flex: 1; border-radius: 8px; height: 46px; border: none; background: #f0f2f5; font-weight: bold; color: #666;">取消</button>
              <button class="btn-primary" @click="handleSubmit" :disabled="loading" style="flex: 1.5; border-radius: 8px; height: 46px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(24,144,255,0.3);">{{ loading ? '提交中...' : '确认上传' }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 成功提示弹窗 -->
    <div
      v-if="showSuccess"
      id="uploadSuccessNotifyModal"
      class="old-modal-mask"
      style="z-index: 100001;"
    >
      <div class="old-modal-box" style="max-width: 320px; text-align: center; background: #ffffff;">
        <div class="old-modal-body" style="padding: 30px;">
          <h3 style="color: #1890ff; font-size: 18px; margin-bottom: 8px;">物料数据上传成功</h3>
          <p style="color: #666; font-size: 13px; line-height: 1.6; white-space: pre-line;">{{ successMessage }}</p>
          <button class="btn-primary" style="margin-top: 20px; padding: 8px 30px; border-radius: 4px;" @click="showSuccess = false">我已知晓</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'

const visible = ref(false)
const loading = ref(false)
const showSuccess = ref(false)
const successMessage = ref('')

const usedValue = ref('')
const producedValue = ref('')
const remarkValue = ref('')
const activeTarget = ref('used')
const remarkTags = ref([])

// 设置活动输入框
const setActiveTarget = (target) => {
  activeTarget.value = target
}

// 按键输入
const pressKey = (key) => {
  const targetMap = {
    used: usedValue,
    produced: producedValue
  }

  const targetRef = targetMap[activeTarget.value]
  if (!targetRef) return

  let currentVal = targetRef.value

  if (key === 'clear') {
    targetRef.value = ''
  } else if (key === 'backspace') {
    targetRef.value = currentVal.substring(0, currentVal.length - 1)
  } else if (key === '.') {
    if (!currentVal.includes('.')) {
      targetRef.value = currentVal + '.'
    }
  } else {
    targetRef.value = currentVal + key
  }
}

// 加载备注标签
const fetchRemarkTags = async () => {
  try {
    const response = await request({ url: '/materials', method: 'GET' })
    remarkTags.value = response.remark_tags || []
  } catch (error) {
    remarkTags.value = []
  }
}

// 打开弹窗
const open = () => {
  usedValue.value = ''
  producedValue.value = ''
  remarkValue.value = ''
  activeTarget.value = 'used'
  visible.value = true
  fetchRemarkTags()
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 提交报表
const handleSubmit = async () => {
  const usedVal = parseFloat(usedValue.value)
  const productVal = parseFloat(producedValue.value)
  const remarkVal = remarkValue.value.trim()

  if (isNaN(usedVal) || isNaN(productVal)) {
    return alert('录入失败：请完整输入耗材与产出量！')
  }

  loading.value = true

  try {
    await request({
      url: '/materials',
      method: 'POST',
      data: {
        used: usedVal,
        produced: productVal,
        remark: remarkVal
      }
    })

    successMessage.value = `物料报表已存入：\n消耗: ${usedVal} kg\n产出: ${productVal} kg${remarkVal ? '\n备注: ' + remarkVal : ''}`
    showSuccess.value = true
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-materials'))
  } catch (error) {
    alert('网络通信异常，提交失败')
  } finally {
    loading.value = false
  }
}

// 暴露方法
defineExpose({
  open
})

// 监听全局事件
onMounted(() => {
  window.addEventListener('open-upload-material-modal', () => {
    open()
  })
})
</script>

<style scoped>
.active-target {
  border-color: #1890ff !important;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}
</style>
