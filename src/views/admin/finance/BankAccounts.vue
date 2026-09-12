<template>
  <div class="bank-accounts-page">
    <!-- 头部 -->
    <header class="page-header">
      <div class="header-left">
        <h2>银行账户</h2>
        <p class="sub-text">管理企业银行账户信息</p>
      </div>
      <button type="button" class="btn-primary" @click="openAddDialog">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M12 5v14m-7-7h14"></path>
        </svg>
        录入账户
      </button>
    </header>

    <!-- 空状态 -->
    <div v-if="!loading && accounts.length === 0" class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <rect x="2" y="7" width="20" height="14" rx="2" />
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
      </svg>
      <p>暂无银行账户</p>
      <button type="button" class="btn-text" @click="openAddDialog">点击添加账户</button>
    </div>

    <!-- 账户卡片网格 -->
    <div v-else class="accounts-grid">
      <!-- 加载骨架屏 -->
      <div v-if="loading" v-for="i in 3" :key="i" class="account-card-skeleton">
        <div class="skeleton-pulse"></div>
      </div>

      <!-- 账户卡片 -->
      <div
        v-for="account in accounts"
        :key="account.id"
        class="bank-card"
        :style="getCardStyle(account)"
        @click="editAccount(account)"
      >
        <div class="bank-card-content">
          <div class="card-header">
            <svg class="chip" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
              <defs>
                <linearGradient id="chipGold" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#f4e5c2;stop-opacity:1" />
                  <stop offset="50%" style="stop-color:#d4af37;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#b8941f;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="chipDark" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#8b7622;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#5c4f15;stop-opacity:1" />
                </linearGradient>
              </defs>
              <!-- 芯片外框 -->
              <rect x="5" y="5" width="40" height="40" rx="6" fill="url(#chipGold)" stroke="#8b7622" stroke-width="0.5"/>
              <!-- 中间网格 -->
              <rect x="12" y="12" width="11" height="11" rx="1" fill="url(#chipDark)"/>
              <rect x="27" y="12" width="11" height="11" rx="1" fill="url(#chipDark)"/>
              <rect x="12" y="27" width="11" height="11" rx="1" fill="url(#chipDark)"/>
              <rect x="27" y="27" width="11" height="11" rx="1" fill="url(#chipDark)"/>
              <!-- 中间分隔线 -->
              <line x1="24" y1="10" x2="24" y2="40" stroke="#8b7622" stroke-width="1"/>
              <line x1="10" y1="24" x2="40" y2="24" stroke="#8b7622" stroke-width="1"/>
              <!-- 光泽效果 -->
              <ellipse cx="15" cy="15" rx="8" ry="8" fill="#f4e5c2" opacity="0.3"/>
            </svg>
            <div class="bank-name-with-icon">
              <img v-if="account.bankIcon" :src="account.bankIcon" alt="银行图标" class="bank-icon" />
              <p class="bank-name">{{ account.bankName }}</p>
            </div>
          </div>

          <div class="card-middle">
            <p class="card-number">{{ formatCardNumber(account.accountNumber) }}</p>
            <div class="card-logo">
              <img src="@/assets/icon/pay.png" alt="UnionPay">
            </div>
          </div>

          <div class="card-footer">
            <div class="card-info">
              <div class="info-item">
                <span class="label">行号</span>
                <span class="value">{{ account.bankCode || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">户名</span>
                <span class="value">{{ account.accountName }}</span>
              </div>
            </div>
            <div class="store-tag">{{ account.storeName }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 账户表单弹窗 -->
    <Teleport to="body">
      <div v-if="dialogVisible" class="modal-overlay" @click.self="closeDialog">
        <div class="modal-container">
          <header class="modal-header">
            <h3>{{ isEditMode ? '修改账户' : '添加账户' }}</h3>
            <button type="button" class="modal-close" @click="closeDialog" aria-label="关闭">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M18 6L6 18M6 6l12 12"></path>
              </svg>
            </button>
          </header>

          <form class="modal-body" @submit.prevent="handleSubmit">
            <div class="form-grid-two-col">
              <label class="field-group">
                <span>所属门店 <em>*</em></span>
                <select v-model="formData.storeId" required>
                  <option value="">请选择门店</option>
                  <option v-for="store in stores" :key="store.id" :value="store.id">
                    {{ store.name }}
                  </option>
                </select>
              </label>

              <label class="field-group">
                <span>账户名称 <em>*</em></span>
                <input
                  v-model.trim="formData.accountName"
                  type="text"
                  placeholder="请输入账户名称"
                  required
                />
              </label>

              <label class="field-group">
                <span>账号 <em>*</em></span>
                <input
                  v-model.trim="formData.accountNumber"
                  type="text"
                  placeholder="请输入银行账号"
                  required
                />
              </label>

              <label class="field-group">
                <span>开户行 <em>*</em></span>
                <input
                  v-model.trim="formData.bankName"
                  type="text"
                  placeholder="请输入开户行名称"
                  required
                />
              </label>

              <label class="field-group field-group-full">
                <span>行号</span>
                <input
                  v-model.trim="formData.bankCode"
                  type="text"
                  placeholder="请输入银行行号"
                />
              </label>

              <label class="field-group">
                <span>背景颜色</span>
                <div class="color-picker-wrapper">
                  <input
                    v-model="formData.cardColor"
                    type="color"
                    class="color-input"
                  />
                  <input
                    v-model="formData.cardColor"
                    type="text"
                    class="color-text"
                    placeholder="#1a1a1a"
                  />
                </div>
              </label>

              <div class="field-group-empty"></div>

              <label class="field-group">
                <span>卡片背景图</span>
                <div class="upload-area">
                  <input
                    ref="bgImageInput"
                    type="file"
                    accept="image/*"
                    style="display: none"
                    @change="handleBgImageUpload"
                  />
                  <button type="button" class="btn-upload" @click="$refs.bgImageInput.click()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"></path>
                    </svg>
                    上传背景图
                  </button>
                  <div v-if="formData.cardBgImage" class="upload-preview bg-preview">
                    <img :src="formData.cardBgImage" alt="背景图" />
                    <button type="button" class="btn-remove-icon" @click="removeBgImage">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </label>

              <label class="field-group">
                <span>银行图标</span>
                <div class="upload-area">
                  <input
                    ref="iconInput"
                    type="file"
                    accept="image/*"
                    style="display: none"
                    @change="handleIconUpload"
                  />
                  <button type="button" class="btn-upload" @click="$refs.iconInput.click()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"></path>
                    </svg>
                    上传图标
                  </button>
                  <div v-if="formData.bankIcon" class="upload-preview icon-preview">
                    <img :src="formData.bankIcon" alt="银行图标" />
                    <button type="button" class="btn-remove-icon" @click="removeIcon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </label>
            </div>

            <footer class="modal-footer">
              <button type="button" class="btn-cancel" @click="closeDialog">取消</button>
              <button type="submit" class="btn-confirm" :disabled="submitting">
                {{ submitting ? '提交中...' : (isEditMode ? '修改' : '添加') }}
              </button>
            </footer>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// import request from '@/utils/request'

const accounts = ref([
  {
    id: 1,
    storeId: 1,
    storeName: '总店',
    accountName: '深圳市某某科技有限公司',
    accountNumber: '6222021234567890123',
    bankName: '中国工商银行深圳分行',
    bankCode: '102584000012'
  },
  {
    id: 2,
    storeId: 2,
    storeName: '分店A',
    accountName: '广州某某贸易有限公司',
    accountNumber: '6225881234567890456',
    bankName: '中国建设银行广州分行',
    bankCode: '105581000023'
  },
  {
    id: 3,
    storeId: 1,
    storeName: '总店',
    accountName: '深圳市某某科技有限公司',
    accountNumber: '6212261234567890789',
    bankName: '中国银行深圳分行',
    bankCode: '104584000034'
  }
])
const stores = ref([
  { id: 1, name: '总店', status: 'active' },
  { id: 2, name: '分店A', status: 'active' },
  { id: 3, name: '分店B', status: 'active' }
])
const loading = ref(false)
const dialogVisible = ref(false)
const isEditMode = ref(false)
const submitting = ref(false)
const formData = ref({
  id: null,
  storeId: '',
  accountName: '',
  accountNumber: '',
  bankName: '',
  bankCode: '',
  cardColor: '#1a1a1a',
  cardBgImage: '',
  bankIcon: ''
})
 

const formatCardNumber = (number) => {
  if (!number) return ''
  return number.replace(/(\d{4})(?=\d)/g, '$1 ')
}

const openAddDialog = () => {
  isEditMode.value = false
  formData.value = {
    id: null,
    storeId: '',
    accountName: '',
    accountNumber: '',
    bankName: '',
    bankCode: '',
    cardColor: '#1a1a1a',
    cardBgImage: '',
    bankIcon: ''
  }
  dialogVisible.value = true
}

const editAccount = (account) => {
  isEditMode.value = true
  formData.value = {
    id: account.id,
    storeId: account.storeId,
    accountName: account.accountName,
    accountNumber: account.accountNumber,
    bankName: account.bankName,
    bankCode: account.bankCode,
    cardColor: account.cardColor || '#1a1a1a',
    cardBgImage: account.cardBgImage || '',
    bankIcon: account.bankIcon || ''
  }
  dialogVisible.value = true
}

const handleIconUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      formData.value.bankIcon = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const handleBgImageUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      formData.value.cardBgImage = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const removeIcon = () => {
  formData.value.bankIcon = ''
}

const removeBgImage = () => {
  formData.value.cardBgImage = ''
}

const getCardStyle = (account) => {
  if (account.cardBgImage) {
    return {
      backgroundImage: `url(${account.cardBgImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  } else if (account.cardColor) {
    return {
      background: `linear-gradient(135deg, ${account.cardColor} 0%, ${adjustColor(account.cardColor, 20)} 100%)`
    }
  } else {
    return {
      background: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)'
    }
  }
}

const adjustColor = (hex, percent) => {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.min(255, ((num >> 16) & 0xFF) + percent)
  const g = Math.min(255, ((num >> 8) & 0xFF) + percent)
  const b = Math.min(255, (num & 0xFF) + percent)
  return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')
}

const closeDialog = () => {
  dialogVisible.value = false
}

const loadAccounts = async () => {
  // loading.value = true
  // try {
  //   const response = await request({
  //     url: '/bank-accounts',
  //     method: 'GET'
  //   })
  //   accounts.value = Array.isArray(response) ? response : []
  // } catch (error) {
  //   console.error('加载账户失败:', error)
  //   accounts.value = []
  // } finally {
  //   loading.value = false
  // }

  // 暂时使用假数据，方便查看样式
  console.log('使用假数据展示')
}

const loadStores = async () => {
  // try {
  //   const response = await request({
  //     url: '/stores',
  //     method: 'GET'
  //   })
  //   stores.value = Array.isArray(response) ? response.filter(s => s.status === 'active') : []
  // } catch (error) {
  //   console.error('加载门店失败:', error)
  //   stores.value = []
  // }

  // 暂时使用假数据
  console.log('使用假数据展示')
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    // const method = isEditMode.value ? 'PUT' : 'POST'
    // const url = isEditMode.value ? `/bank-accounts/${formData.value.id}` : '/bank-accounts'

    // await request({
    //   url,
    //   method,
    //   data: {
    //     storeId: formData.value.storeId,
    //     accountName: formData.value.accountName,
    //     accountNumber: formData.value.accountNumber,
    //     bankName: formData.value.bankName,
    //     bankCode: formData.value.bankCode
    //   }
    // })

    // 模拟添加/修改
    const storeName = stores.value.find(s => s.id === Number(formData.value.storeId))?.name || '未知门店'

    if (isEditMode.value) {
      const index = accounts.value.findIndex(a => a.id === formData.value.id)
      if (index > -1) {
        accounts.value[index] = {
          ...formData.value,
          storeName
        }
      }
    } else {
      accounts.value.push({
        id: Date.now(),
        ...formData.value,
        storeName
      })
    }

    window.alert(`账户${isEditMode.value ? '修改' : '添加'}成功`)
    closeDialog()
    // loadAccounts()
  } catch (error) {
    console.error('保存账户失败:', error)
    window.alert(error?.response?.data?.error || `账户${isEditMode.value ? '修改' : '添加'}失败`)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadAccounts()
  loadStores()
})
</script>

<style scoped>
.bank-accounts-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;

  min-height: 100%;
  background: var(--page-bg);
  color: var(--text);
  font-size: 14px;
}

/* 页头 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  margin: 14px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.header-left h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 4px;
}

.sub-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  margin: 14px;
}

.empty-state svg {
  width: 48px;
  height: 48px;
  color: var(--text-muted);
  stroke-width: 1.5;
  margin-bottom: 12px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0 0 12px;
}

/* 账户网格 */
.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
  gap: 20px;
  padding: 14px;
}

/* 加载骨架屏 */
.account-card-skeleton {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  height: 308px;
  overflow: hidden;
}

.skeleton-pulse {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(15, 23, 42, 0.03), transparent);
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
}

/* 银行卡样式 */
.bank-card {
  border-radius: 16px;
  padding: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.bank-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(213, 0, 0, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.bank-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
}

.bank-card:hover::before {
  opacity: 1;
}

.bank-card-content {
  position: relative;
  z-index: 1;
  color: #F8FAFC;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 40px;
}

.chip {
  width: 50px;
  height: 50px;
  flex-shrink: 0;
}

.bank-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0;
  color: #F8FAFC;
  white-space: nowrap;
}

.bank-name-with-icon {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.bank-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
  border-radius: 4px;
}

.card-middle {
  margin-bottom: 30px;
  position: relative;
}

.card-number {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
  margin: 0 0 20px;
  font-variant-numeric: tabular-nums;
}

.card-logo {
  position: absolute;
  right: -8px;
  bottom: -108px;
  width: 80px;
  height: 50px;
}

.card-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.card-info {
  flex: 1;
}

.info-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 8px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .label {
  font-size: 10px;
  color: rgba(248, 250, 252, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.info-item .value {
  font-size: 13px;
  font-weight: 500;
  color: #F8FAFC;
}

.store-tag {
  background: rgba(15, 159, 120, 0.2);
  color: var(--accent);
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

/* 按钮 */
.btn-primary, .btn-text {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 38px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.25);
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 18px;
  height: 18px;
  stroke-width: 2;
}

.btn-text {
  background: transparent;
  color: var(--accent-dark);
  padding: 8px 12px;
}

.btn-text:hover {
  background: var(--accent-soft);
  color: var(--accent-dark);
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
}

.modal-container {
  background: #ffffff;
  border-radius: 7px;
  border: 1px solid #e2e8f0;
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #172033;
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #596579;
  cursor: pointer;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.18s ease;
  padding: 0;
}

.modal-close:hover {
  background: #f1f5f9;
  color: #172033;
}

.modal-close svg {
  width: 18px;
  height: 18px;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  background: #ffffff;
}

.form-grid-two-col {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-group-full {
  grid-column: 1 / -1;
}

.field-group-empty {
  /* 占位元素，用于保持网格布局 */
}

.field-group span {
  font-size: 13px;
  font-weight: 600;
  color: #172033;
}

.field-group em {
  color: #ef4444;
  font-style: normal;
}

.field-group input,
.field-group select {
  height: 38px;
  padding: 0 11px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  font-size: 14px;
  color: #172033;
  transition: all 0.18s ease;
}

.field-group input:focus,
.field-group select:focus {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
  border-color: #0f9f78;
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.1);
}

.field-group input::placeholder {
  color: #8a96a8;
}

/* 颜色选择器 */
.color-picker-wrapper {
  display: flex;
  gap: 8px;
  align-items: center;
}

.color-input {
  width: 60px;
  height: 38px;
  padding: 4px;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
}

.color-text {
  flex: 1;
  height: 38px;
  padding: 0 11px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  font-size: 14px;
  color: #172033;
  font-family: 'Courier New', monospace;
}

.color-text:focus {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
  border-color: #0f9f78;
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.1);
}

/* 上传区域 */
.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-upload {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 38px;
  padding: 0 16px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  color: #596579;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.btn-upload:hover {
  background: #e9f8f3;
  border-color: #a9e5d2;
  color: #08745a;
}

.btn-upload svg {
  width: 16px;
  height: 16px;
}

.upload-preview {
  position: relative;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  overflow: hidden;
  background: #f8fafc;
  flex-shrink: 0;
}

.bg-preview {
  width: 100px;
  height: 62px;
}

.bg-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.icon-preview {
  width: 60px;
  height: 60px;
}

.icon-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.btn-remove-icon {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: rgba(239, 68, 68, 0.9);
  border: none;
  border-radius: 3px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.18s ease;
}

.btn-remove-icon:hover {
  background: #ef4444;
}

.btn-remove-icon svg {
  width: 12px;
  height: 12px;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  background: #ffffff;
}

.btn-cancel,
.btn-confirm {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  padding: 0 32px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  min-width: 120px;
  cursor: pointer;
  transition: all 0.18s ease;
  border: 1px solid transparent;
}

.btn-cancel {
  background: #ffffff;
  color: #596579;
  border-color: #cbd5e1;
}

.btn-cancel:hover {
  background: #e9f8f3;
  border-color: #a9e5d2;
  color: #08745a;
}

.btn-confirm {
  background: #0f9f78;
  color: #ffffff;
  border-color: #0f9f78;
}

.btn-confirm:hover:not(:disabled) {
  background: #08745a;
  border-color: #08745a;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(15, 159, 120, 0.25);
}

.btn-confirm:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 780px) {
  .accounts-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .modal-container {
    width: calc(100vw - 32px);
    max-width: calc(100vw - 32px);
  }

  .form-grid-two-col {
    grid-template-columns: 1fr;
  }
}
</style>
