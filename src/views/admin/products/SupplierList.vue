<template>
  <div class="supplier-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">采购协同</p>
        <h1>供应商管理</h1>
        <p class="page-description">维护供应商基础资料，统一用于采购入库和对账。</p>
      </div>
      <button class="btn btn-primary" type="button" @click="openCreate">
        <svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17">
          <path d="M12 5v14M5 12h14" />
        </svg>
        新增供应商
      </button>
    </header>

    <section class="filter-panel" aria-label="供应商筛选">
      <div class="filter-heading">
        <div>
          <h2>筛选条件</h2>
          <span>支持按供应商信息快速定位</span>
        </div>
        <span class="result-count">共 {{ filteredSuppliers.length }} 条</span>
      </div>
      <div class="filter-grid">
        <label class="field">
          <span>供应商名称</span>
          <input
            v-model.trim="filters.supplierName"
            type="search"
            placeholder="搜索供应商名称"
            @keyup.enter="handleSearch"
          />
        </label>
        <label class="field">
          <span>供应商编号</span>
          <input
            v-model.trim="filters.supplierCode"
            type="search"
            placeholder="如 SUP-001"
            @keyup.enter="handleSearch"
          />
        </label>
        <label class="field">
          <span>联系人</span>
          <input
            v-model.trim="filters.contactPerson"
            type="search"
            placeholder="搜索联系人"
            @keyup.enter="handleSearch"
          />
        </label>
        <label class="field">
          <span>联系电话</span>
          <input
            v-model.trim="filters.phone"
            type="search"
            placeholder="搜索联系电话"
            @keyup.enter="handleSearch"
          />
        </label>
        <label class="field">
          <span>所属门店</span>
          <select v-model="filters.storeId" @change="handleSearch">
            <option value="">全部门店</option>
            <option v-for="store in stores" :key="store.id" :value="String(store.id)">
              {{ store.name || store.storeName }}
            </option>
          </select>
        </label>
        <label class="field">
          <span>供应商状态</span>
          <select v-model="filters.status" @change="handleSearch">
            <option value="">全部状态</option>
            <option value="active">启用</option>
            <option value="inactive">停用</option>
          </select>
        </label>
        <div class="filter-actions">
          <button class="btn btn-primary btn-search" type="button" @click="handleSearch">
            <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
              <circle cx="10.8" cy="10.8" r="6.8" />
              <path d="m16 16 5 5" />
            </svg>
            查询
          </button>
          <button class="btn btn-ghost" type="button" @click="resetFilters">
            <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
              <path d="M4 12a8 8 0 1 0 2.3-5.7" />
              <path d="M4 4v5h5" />
            </svg>
            重置
          </button>
        </div>
      </div>
    </section>

    <section class="table-card">
      <div class="table-toolbar">
        <div>
          <h2>供应商档案</h2>
          <span class="toolbar-note">最后同步：{{ lastLoadedAt || '尚未同步' }}</span>
        </div>
        <button class="icon-button" type="button" title="刷新供应商列表" aria-label="刷新供应商列表" :disabled="loading" @click="loadSuppliers">
          <svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17" :class="{ spinning: loading }">
            <path d="M20 11a8 8 0 0 0-14.9-4L3 9" />
            <path d="M3 4v5h5" />
            <path d="M4 13a8 8 0 0 0 14.9 4L21 15" />
            <path d="M21 20v-5h-5" />
          </svg>
        </button>
      </div>

      <div class="table-wrap">
        <table class="supplier-table">
          <thead>
            <tr>
              <th>供应商编号</th>
              <th>供应商名称</th>
              <th>所属门店</th>
              <th>联系人</th>
              <th>联系电话</th>
              <th>开户银行</th>
              <th>税号</th>
              <th>状态</th>
              <th>创建时间</th>
              <th class="actions-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="10" class="state-cell">
                <span class="loader" aria-hidden="true"></span>
                正在加载供应商...
              </td>
            </tr>
            <tr v-else-if="paginatedSuppliers.length === 0">
              <td colspan="10" class="state-cell empty-state">
                <span class="empty-symbol" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="32" height="32">
                    <path d="M4 8.5 12 4l8 4.5v8L12 21l-8-4.5z" />
                    <path d="m4 8.5 8 4.5 8-4.5M12 13v8" />
                  </svg>
                </span>
                <strong>{{ errorMessage ? '暂时无法显示供应商' : '暂无匹配的供应商' }}</strong>
                <span>{{ errorMessage || '调整筛选条件，或点击“新增供应商”建立第一条档案。' }}</span>
                <button v-if="errorMessage" class="btn btn-ghost state-retry" type="button" @click="loadSuppliers">重新加载</button>
              </td>
            </tr>
            <template v-else>
              <tr v-for="supplier in paginatedSuppliers" :key="supplier.id">
              <td>
                <button class="code-link" type="button" @click="openDetail(supplier)">
                  {{ supplier.supplierCode || '未设置' }}
                </button>
              </td>
              <td>
                <button class="name-link" type="button" @click="openDetail(supplier)">
                  <span class="supplier-avatar">{{ getInitial(supplier.supplierName) }}</span>
                  <span>
                    <strong>{{ supplier.supplierName }}</strong>
                    <small>{{ supplier.remark || '暂无备注' }}</small>
                  </span>
                </button>
              </td>
              <td>{{ storeName(supplier.storeId) }}</td>
              <td>{{ supplier.contactPerson || '-' }}</td>
              <td class="phone-cell">{{ supplier.phone || '-' }}</td>
              <td>{{ supplier.bankName || '-' }}</td>
              <td class="tax-cell">{{ supplier.taxNumber || '-' }}</td>
              <td>
                <span class="status-pill" :class="supplier.status === 'inactive' ? 'inactive' : 'active'">
                  <i aria-hidden="true"></i>
                  {{ statusLabel(supplier.status) }}
                </span>
              </td>
              <td class="date-cell">{{ formatDate(supplier.createdAt) }}</td>
              <td class="actions-column">
                <div class="row-actions">
                  <button class="row-action view" type="button" title="查看详情" aria-label="查看详情" @click="openDetail(supplier)">
                    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
                      <path d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z" />
                      <circle cx="12" cy="12" r="2.5" />
                    </svg>
                  </button>
                  <button class="row-action edit" type="button" title="编辑供应商" aria-label="编辑供应商" @click="openEdit(supplier)">
                    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
                      <path d="m4 16-.8 4.8L8 20l11.5-11.5a2.8 2.8 0 0 0-4-4Z" />
                      <path d="m13.5 6.5 4 4" />
                    </svg>
                  </button>
                  <button class="row-action delete" type="button" title="删除供应商" aria-label="删除供应商" @click="handleDelete(supplier)">
                    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
                      <path d="M4 7h16M9 7V4h6v3m-9 0 1 13h10l1-13M10 11v5m4-5v5" />
                    </svg>
                  </button>
                </div>
              </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <footer class="table-footer">
        <span>显示 {{ paginationStart }}-{{ paginationEnd }}，共 {{ filteredSuppliers.length }} 条</span>
        <div class="pagination-controls">
          <label>
            <span class="sr-only">每页条数</span>
            <select v-model.number="pageSize" aria-label="每页条数">
              <option :value="10">10 条/页</option>
              <option :value="20">20 条/页</option>
              <option :value="50">50 条/页</option>
            </select>
          </label>
          <button type="button" :disabled="currentPage <= 1" @click="changePage(currentPage - 1)">上一页</button>
          <span class="page-number">{{ currentPage }} / {{ totalPages }}</span>
          <button type="button" :disabled="currentPage >= totalPages" @click="changePage(currentPage + 1)">下一页</button>
        </div>
      </footer>
    </section>

    <div v-if="notice.message" class="notice" :class="'notice-' + notice.type" role="status">
      <svg v-if="notice.type === 'success'" aria-hidden="true" viewBox="0 0 24 24" width="18" height="18">
        <path d="m5 12 4 4L19 6" />
      </svg>
      <svg v-else aria-hidden="true" viewBox="0 0 24 24" width="18" height="18">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v5M12 16.5v.1" />
      </svg>
      <span>{{ notice.message }}</span>
      <button type="button" aria-label="关闭提示" @click="notice.message = ''">×</button>
    </div>

    <!-- supplier detail -->
    <div v-if="detailSupplier" class="modal-overlay" @click.self="closeDetail">
      <aside class="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="supplier-detail-title">
        <div class="modal-header">
          <div>
            <p class="eyebrow">供应商档案</p>
            <h2 id="supplier-detail-title">{{ detailSupplier.supplierName }}</h2>
          </div>
          <button class="close-button" type="button" title="关闭详情" aria-label="关闭详情" @click="closeDetail">×</button>
        </div>
        <div class="detail-body">
          <div class="detail-code-row">
            <span class="detail-code">{{ detailSupplier.supplierCode || '未设置编号' }}</span>
            <span class="status-pill" :class="detailSupplier.status === 'inactive' ? 'inactive' : 'active'">
              <i aria-hidden="true"></i>{{ statusLabel(detailSupplier.status) }}
            </span>
          </div>
          <section class="detail-section">
            <h3>基本信息</h3>
            <dl class="detail-grid">
              <div><dt>所属门店</dt><dd>{{ storeName(detailSupplier.storeId) }}</dd></div>
              <div><dt>联系人</dt><dd>{{ detailSupplier.contactPerson || '-' }}</dd></div>
              <div><dt>联系电话</dt><dd>{{ detailSupplier.phone || '-' }}</dd></div>
              <div class="detail-wide"><dt>联系地址</dt><dd>{{ detailSupplier.address || '-' }}</dd></div>
            </dl>
          </section>
          <section class="detail-section">
            <h3>结算信息</h3>
            <dl class="detail-grid">
              <div><dt>开户银行</dt><dd>{{ detailSupplier.bankName || '-' }}</dd></div>
              <div><dt>银行账号</dt><dd>{{ detailSupplier.bankAccount || '-' }}</dd></div>
              <div class="detail-wide"><dt>税号</dt><dd>{{ detailSupplier.taxNumber || '-' }}</dd></div>
            </dl>
          </section>
          <section class="detail-section">
            <h3>备注</h3>
            <p class="detail-remark">{{ detailSupplier.remark || '暂无备注' }}</p>
          </section>
          <p class="detail-meta">创建于 {{ formatDate(detailSupplier.createdAt) }}<span v-if="detailSupplier.updatedAt">，更新于 {{ formatDate(detailSupplier.updatedAt) }}</span></p>
        </div>
        <div class="detail-footer">
          <button class="btn btn-ghost" type="button" @click="closeDetail">关闭</button>
          <button class="btn btn-primary" type="button" @click="openEdit(detailSupplier)">编辑资料</button>
        </div>
      </aside>
    </div>

    <!-- create / edit form -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="form-modal" role="dialog" aria-modal="true" aria-labelledby="supplier-form-title">
        <div class="modal-header">
          <div>
            <p class="eyebrow">{{ isEditMode ? '资料维护' : '建立档案' }}</p>
            <h2 id="supplier-form-title">{{ isEditMode ? '编辑供应商' : '新增供应商' }}</h2>
          </div>
          <button class="close-button" type="button" title="关闭弹窗" aria-label="关闭弹窗" @click="closeForm">×</button>
        </div>
        <form class="supplier-form" novalidate @submit.prevent="handleSubmit">
          <section class="form-section">
            <h3>基本信息</h3>
            <div class="form-grid">
              <label class="form-field required-field">
                <span>供应商名称 <em>*</em></span>
                <input v-model.trim="form.supplierName" type="text" maxlength="120" placeholder="请输入供应商名称" :class="{ invalid: errors.supplierName }" @blur="validateField('supplierName')" />
                <small v-if="errors.supplierName">{{ errors.supplierName }}</small>
              </label>
              <label class="form-field">
                <span>供应商编号</span>
                <input v-model.trim="form.supplierCode" type="text" maxlength="60" placeholder="选填，需保持唯一" :class="{ invalid: errors.supplierCode }" />
                <small v-if="errors.supplierCode">{{ errors.supplierCode }}</small>
              </label>
              <label class="form-field">
                <span>所属门店</span>
                <select v-model="form.storeId">
                  <option value="">通用供应商（不限定门店）</option>
                  <option v-for="store in stores" :key="store.id" :value="String(store.id)">{{ store.name || store.storeName }}</option>
                </select>
              </label>
              <label class="form-field">
                <span>状态</span>
                <select v-model="form.status">
                  <option value="active">启用</option>
                  <option value="inactive">停用</option>
                </select>
              </label>
              <label class="form-field">
                <span>联系人</span>
                <input v-model.trim="form.contactPerson" type="text" maxlength="80" placeholder="请输入联系人" />
              </label>
              <label class="form-field">
                <span>联系电话</span>
                <input v-model.trim="form.phone" type="tel" maxlength="40" placeholder="请输入联系电话" :class="{ invalid: errors.phone }" />
                <small v-if="errors.phone">{{ errors.phone }}</small>
              </label>
              <label class="form-field full-field">
                <span>联系地址</span>
                <input v-model.trim="form.address" type="text" maxlength="240" placeholder="请输入联系地址" />
              </label>
            </div>
          </section>
          <section class="form-section">
            <h3>结算信息</h3>
            <div class="form-grid">
              <label class="form-field">
                <span>开户银行</span>
                <input v-model.trim="form.bankName" type="text" maxlength="120" placeholder="请输入开户银行" />
              </label>
              <label class="form-field">
                <span>银行账号</span>
                <input v-model.trim="form.bankAccount" type="text" maxlength="120" placeholder="请输入银行账号" />
              </label>
              <label class="form-field full-field">
                <span>税号</span>
                <input v-model.trim="form.taxNumber" type="text" maxlength="80" placeholder="请输入税号" />
              </label>
              <label class="form-field full-field">
                <span>备注</span>
                <textarea v-model.trim="form.remark" maxlength="500" rows="3" placeholder="补充付款周期、交付要求等信息"></textarea>
              </label>
            </div>
          </section>
          <div class="form-actions">
            <button class="btn btn-ghost" type="button" :disabled="saving" @click="closeForm">取消</button>
            <button class="btn btn-primary" type="submit" :disabled="saving">
              <span v-if="saving" class="button-loader" aria-hidden="true"></span>
              {{ saving ? '保存中...' : (isEditMode ? '保存修改' : '创建供应商') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import request from '@/api/request'

const suppliers = ref([])
const stores = ref([])
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const lastLoadedAt = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const showForm = ref(false)
const isEditMode = ref(false)
const editingSupplierId = ref(null)
const detailSupplier = ref(null)
const notice = reactive({ type: 'success', message: '' })
let noticeTimer = null

const filters = reactive({
  supplierName: '',
  supplierCode: '',
  contactPerson: '',
  phone: '',
  storeId: '',
  status: ''
})

const emptyForm = () => ({
  supplierCode: '',
  supplierName: '',
  storeId: '',
  contactPerson: '',
  phone: '',
  address: '',
  taxNumber: '',
  bankName: '',
  bankAccount: '',
  remark: '',
  status: 'active'
})

const form = reactive(emptyForm())
const errors = reactive({ supplierName: '', supplierCode: '', phone: '' })

const storeMap = computed(() => new Map(stores.value.map(store => [String(store.id), store.name || store.storeName || '未知门店'])))

const filteredSuppliers = computed(() => {
  const name = filters.supplierName.toLowerCase()
  const code = filters.supplierCode.toLowerCase()
  const contact = filters.contactPerson.toLowerCase()
  const phone = filters.phone.toLowerCase()
  return suppliers.value.filter(supplier => {
    const matchesName = !name || supplier.supplierName.toLowerCase().includes(name)
    const matchesCode = !code || supplier.supplierCode.toLowerCase().includes(code)
    const matchesContact = !contact || supplier.contactPerson.toLowerCase().includes(contact)
    const matchesPhone = !phone || supplier.phone.toLowerCase().includes(phone)
    const matchesStore = !filters.storeId || String(supplier.storeId ?? '') === String(filters.storeId)
    const matchesStatus = !filters.status || supplier.status === filters.status
    return matchesName && matchesCode && matchesContact && matchesPhone && matchesStore && matchesStatus
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredSuppliers.value.length / pageSize.value)))
const paginatedSuppliers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredSuppliers.value.slice(start, start + pageSize.value)
})
const paginationStart = computed(() => filteredSuppliers.value.length ? (currentPage.value - 1) * pageSize.value + 1 : 0)
const paginationEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredSuppliers.value.length))

watch(
  () => [filters.supplierName, filters.supplierCode, filters.contactPerson, filters.phone, filters.storeId, filters.status, pageSize.value],
  () => {
    currentPage.value = 1
  }
)
watch(totalPages, value => {
  if (currentPage.value > value) currentPage.value = value
})

const normalizeSupplier = source => {
  const item = source || {}
  return {
    ...item,
    id: item.id,
    supplierCode: String(item.supplierCode ?? item.supplier_code ?? item.code ?? '').trim(),
    supplierName: String(item.supplierName ?? item.supplier_name ?? item.name ?? '').trim(),
    storeId: item.storeId ?? item.store_id ?? '',
    contactPerson: String(item.contactPerson ?? item.contact_person ?? '').trim(),
    phone: String(item.phone ?? '').trim(),
    address: String(item.address ?? '').trim(),
    taxNumber: String(item.taxNumber ?? item.tax_number ?? '').trim(),
    bankName: String(item.bankName ?? item.bank_name ?? '').trim(),
    bankAccount: String(item.bankAccount ?? item.bank_account ?? '').trim(),
    remark: String(item.remark ?? '').trim(),
    status: String(item.status || 'active').toLowerCase(),
    createdAt: item.createdAt ?? item.created_at ?? '',
    updatedAt: item.updatedAt ?? item.updated_at ?? ''
  }
}

const extractList = response => {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.suppliers)) return response.suppliers
  if (Array.isArray(response?.data)) return response.data
  return []
}

const extractError = (error, fallback) => {
  return error?.response?.data?.message
    || error?.response?.data?.error
    || error?.message
    || fallback
}

const showNotice = (message, type = 'success') => {
  notice.type = type
  notice.message = message
  if (noticeTimer) window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.message = ''
  }, 4200)
}

const loadStores = async () => {
  try {
    const response = await request({ url: '/stores', method: 'GET' })
    stores.value = extractList(response)
      .filter(store => store && store.id !== undefined && store.id !== null)
      .map(store => ({ ...store, id: store.id, name: store.name || store.storeName || store.store_name || ('门店 ' + store.id) }))
  } catch (error) {
    stores.value = []
    showNotice(extractError(error, '门店列表加载失败，供应商仍可保存为通用资料'), 'error')
  }
}

const loadSuppliers = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await request({ url: '/suppliers', method: 'GET' })
    suppliers.value = extractList(response).map(normalizeSupplier)
    lastLoadedAt.value = formatDateTime(new Date())
  } catch (error) {
    suppliers.value = []
    errorMessage.value = extractError(error, '请检查后端服务后重试')
    showNotice(errorMessage.value, 'error')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadSuppliers()
}

const resetFilters = () => {
  Object.assign(filters, {
    supplierName: '',
    supplierCode: '',
    contactPerson: '',
    phone: '',
    storeId: '',
    status: ''
  })
  currentPage.value = 1
}

const resetForm = () => {
  Object.assign(form, emptyForm())
  Object.assign(errors, { supplierName: '', supplierCode: '', phone: '' })
}

const openCreate = () => {
  detailSupplier.value = null
  isEditMode.value = false
  editingSupplierId.value = null
  resetForm()
  showForm.value = true
}

const openEdit = supplier => {
  detailSupplier.value = null
  isEditMode.value = true
  editingSupplierId.value = supplier.id
  Object.assign(form, {
    supplierCode: supplier.supplierCode,
    supplierName: supplier.supplierName,
    storeId: supplier.storeId === null || supplier.storeId === undefined ? '' : String(supplier.storeId),
    contactPerson: supplier.contactPerson,
    phone: supplier.phone,
    address: supplier.address,
    taxNumber: supplier.taxNumber,
    bankName: supplier.bankName,
    bankAccount: supplier.bankAccount,
    remark: supplier.remark,
    status: supplier.status === 'inactive' ? 'inactive' : 'active'
  })
  Object.assign(errors, { supplierName: '', supplierCode: '', phone: '' })
  showForm.value = true
}

const closeForm = () => {
  if (!saving.value) showForm.value = false
}

const validateField = field => {
  if (field === 'supplierName') {
    errors.supplierName = form.supplierName.trim() ? '' : '请输入供应商名称'
  }
  if (field === 'phone') {
    errors.phone = form.phone && !/^[0-9+()（）\\-\\s]{6,40}$/.test(form.phone) ? '联系电话格式不正确' : ''
  }
  return !errors.supplierName && !errors.phone
}

const validateForm = () => {
  validateField('supplierName')
  validateField('phone')
  errors.supplierCode = form.supplierCode.length > 60 ? '编号不能超过 60 个字符' : ''
  return !errors.supplierName && !errors.supplierCode && !errors.phone
}

const handleSubmit = async () => {
  if (!validateForm()) return
  saving.value = true
  const payload = {
    supplierCode: form.supplierCode.trim(),
    supplierName: form.supplierName.trim(),
    storeId: form.storeId ? Number(form.storeId) : null,
    contactPerson: form.contactPerson.trim(),
    phone: form.phone.trim(),
    address: form.address.trim(),
    taxNumber: form.taxNumber.trim(),
    bankName: form.bankName.trim(),
    bankAccount: form.bankAccount.trim(),
    remark: form.remark.trim(),
    status: form.status
  }
  try {
    const response = await request({
      url: isEditMode.value ? '/suppliers/' + editingSupplierId.value : '/suppliers',
      method: isEditMode.value ? 'PUT' : 'POST',
      data: payload
    })
    const message = response?.message || (isEditMode.value ? '供应商资料已更新' : '供应商创建成功')
    showForm.value = false
    showNotice(message)
    await loadSuppliers()
  } catch (error) {
    showNotice(extractError(error, '保存供应商失败'), 'error')
  } finally {
    saving.value = false
  }
}

const handleDelete = async supplier => {
  const confirmed = window.confirm('确定删除供应商“' + supplier.supplierName + '”吗？已被入库单引用的资料将自动停用。')
  if (!confirmed) return
  try {
    const response = await request({ url: '/suppliers/' + supplier.id, method: 'DELETE' })
    showNotice(response?.message || '供应商已删除')
    await loadSuppliers()
  } catch (error) {
    showNotice(extractError(error, '删除供应商失败'), 'error')
  }
}

const openDetail = supplier => {
  detailSupplier.value = supplier
}

const closeDetail = () => {
  detailSupplier.value = null
}

const changePage = page => {
  if (page >= 1 && page <= totalPages.value) currentPage.value = page
}

const storeName = storeId => {
  if (storeId === null || storeId === undefined || storeId === '') return '通用供应商'
  return storeMap.value.get(String(storeId)) || '未知门店'
}

const statusLabel = status => status === 'inactive' ? '已停用' : '启用中'

const getInitial = name => (name || '供').trim().slice(0, 1).toUpperCase()

const formatDate = value => {
  if (!value) return '-'
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10)
  return date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0')
}

const formatDateTime = value => {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) return ''
  return formatDate(value) + ' ' + String(value.getHours()).padStart(2, '0') + ':' + String(value.getMinutes()).padStart(2, '0')
}

defineExpose({ loadSuppliers, openCreate, openEdit })

onMounted(async () => {
  await loadStores()
  await loadSuppliers()
})
</script>

<style scoped>
.supplier-page,
.supplier-page * {
  box-sizing: border-box;
}

.supplier-page {
  --ink: #17212b;
  --muted: #6f7b87;
  --line: #e5e9ed;
  --panel: #ffffff;
  --canvas: #f5f7f8;
  --accent: #159a7c;
  --accent-dark: #08755e;
  min-height: 100%;
  padding: 28px 32px 42px;
  color: var(--ink);
  background: var(--canvas);
}

.page-header,
.table-toolbar,
.filter-heading,
.table-footer,
.modal-header,
.detail-footer,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header {
  margin: 0 auto 24px;
  max-width: 1600px;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--accent-dark);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .14em;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 8px;
  font-size: 30px;
  line-height: 1.2;
  letter-spacing: 0;
}

.page-description {
  margin-bottom: 0;
  color: var(--muted);
  font-size: 13px;
}

h2 {
  margin-bottom: 5px;
  font-size: 17px;
}

.filter-panel,
.table-card {
  max-width: 1600px;
  margin: 0 auto 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: 0 5px 18px rgba(23, 33, 43, .04);
}

.filter-panel {
  padding: 20px 22px 22px;
}

.filter-heading span,
.toolbar-note {
  color: var(--muted);
  font-size: 12px;
}

.result-count {
  padding: 6px 11px;
  border-radius: 999px;
  color: #08755e !important;
  background: #e8f6f1;
  font-variant-numeric: tabular-nums;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(130px, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.field,
.form-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
  color: #566371;
  font-size: 12px;
  font-weight: 600;
}

input,
select,
textarea {
  width: 100%;
  border: 1px solid #d8dfe4;
  border-radius: 5px;
  outline: none;
  color: var(--ink);
  background: #fff;
  font: inherit;
  font-weight: 400;
  transition: border-color .18s, box-shadow .18s;
}

input,
select {
  height: 38px;
  padding: 0 11px;
}

textarea {
  min-height: 84px;
  padding: 10px 11px;
  resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
  border-color: #47b79d;
  box-shadow: 0 0 0 3px rgba(21, 154, 124, .12);
}

input::placeholder,
textarea::placeholder {
  color: #a5afb7;
}

.filter-actions {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  grid-column: span 2;
}

.btn {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  transition: background .18s, border-color .18s, color .18s, transform .18s;
}

.btn:active {
  transform: translateY(1px);
}

.btn:disabled,
.icon-button:disabled,
.row-action:disabled {
  cursor: not-allowed;
  opacity: .55;
}

.btn-primary {
  border-color: var(--accent);
  color: #fff;
  background: var(--accent);
}

.btn-primary:hover:not(:disabled) {
  border-color: var(--accent-dark);
  background: var(--accent-dark);
}

.btn-ghost {
  border-color: #d8dfe4;
  color: #4d5b67;
  background: #fff;
}

.btn-ghost:hover:not(:disabled) {
  border-color: #9db4ad;
  color: var(--accent-dark);
  background: #f5fbf9;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.table-card {
  overflow: hidden;
}

.table-toolbar {
  padding: 19px 22px;
  border-bottom: 1px solid var(--line);
}

.icon-button,
.close-button,
.row-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  cursor: pointer;
  color: #65727e;
  background: transparent;
}

.icon-button {
  width: 34px;
  height: 34px;
  border-color: #dfe5e8;
  border-radius: 5px;
}

.icon-button:hover {
  color: var(--accent-dark);
  border-color: #9cc9bd;
  background: #f1faf7;
}

.spinning {
  animation: spin .9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-wrap {
  overflow-x: auto;
}

.supplier-table {
  width: 100%;
  min-width: 1040px;
  border-collapse: collapse;
  font-size: 13px;
}

th,
td {
  padding: 13px 15px;
  border-bottom: 1px solid #edf0f2;
  text-align: left;
  white-space: nowrap;
}

th {
  color: #7a8791;
  background: #fbfcfc;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .03em;
}

tbody tr {
  transition: background .16s;
}

tbody tr:hover {
  background: #fbfdfd;
}

tbody tr:last-child td {
  border-bottom: 0;
}

.code-link,
.name-link {
  border: 0;
  cursor: pointer;
  font: inherit;
  text-align: left;
  background: transparent;
}

.code-link {
  color: var(--accent-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
}

.code-link:hover,
.name-link:hover strong {
  text-decoration: underline;
}

.name-link {
  display: flex;
  min-width: 190px;
  align-items: center;
  gap: 9px;
}

.name-link > span:last-child {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.name-link strong {
  color: var(--ink);
  font-weight: 650;
}

.name-link small {
  max-width: 190px;
  overflow: hidden;
  color: #9aa5ae;
  font-size: 11px;
  text-overflow: ellipsis;
}

.supplier-avatar {
  display: inline-flex;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #08755e;
  background: #e5f5ef;
  font-size: 14px;
  font-weight: 750;
}

.phone-cell,
.tax-cell,
.date-cell {
  font-variant-numeric: tabular-nums;
}

.tax-cell {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-pill.active {
  color: #08755e;
  background: #e5f5ef;
}

.status-pill.inactive {
  color: #7d5960;
  background: #f3ecee;
}

.actions-column {
  text-align: right;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 3px;
}

.row-action {
  width: 30px;
  height: 30px;
  border-radius: 4px;
}

.row-action:hover {
  background: #f0f4f4;
}

.row-action.view:hover {
  color: #2378a6;
}

.row-action.edit:hover {
  color: var(--accent-dark);
}

.row-action.delete:hover {
  color: #b54e57;
  background: #fff3f3;
}

.state-cell {
  height: 220px;
  color: #76838d;
  text-align: center;
  vertical-align: middle;
}

.loader {
  display: inline-block;
  width: 17px;
  height: 17px;
  margin-right: 8px;
  vertical-align: -4px;
  border: 2px solid #dcebe6;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}

.empty-state {
  display: table-cell;
  padding: 35px 20px;
}

.empty-state > * {
  display: block;
  margin: 0 auto 8px;
}

.empty-state strong {
  color: #46535e;
}

.empty-state span:not(.empty-symbol) {
  color: #98a3ab;
  font-size: 12px;
}

.empty-symbol {
  color: #9bb9b1;
}

.state-retry {
  margin-top: 15px !important;
}

.table-footer {
  min-height: 62px;
  padding: 12px 22px;
  border-top: 1px solid var(--line);
  color: #87929b;
  font-size: 12px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-controls select,
.pagination-controls button {
  height: 32px;
  padding: 0 9px;
  border: 1px solid #dbe1e5;
  border-radius: 4px;
  color: #5e6a74;
  background: #fff;
  font: inherit;
  font-size: 12px;
}

.pagination-controls button {
  cursor: pointer;
}

.pagination-controls button:hover:not(:disabled) {
  color: var(--accent-dark);
  border-color: #a2c8be;
}

.pagination-controls button:disabled {
  cursor: not-allowed;
  opacity: .45;
}

.page-number {
  min-width: 54px;
  color: #53616c;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.notice {
  position: fixed;
  z-index: 50;
  top: 76px;
  right: 25px;
  display: flex;
  max-width: min(390px, calc(100vw - 32px));
  align-items: center;
  gap: 9px;
  padding: 12px 13px;
  border: 1px solid;
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(26, 38, 46, .14);
  font-size: 13px;
  animation: notice-in .2s ease-out;
}

.notice button {
  margin-left: auto;
  padding: 0 3px;
  border: 0;
  cursor: pointer;
  color: inherit;
  background: transparent;
  font-size: 20px;
  line-height: 1;
}

.notice-success {
  border-color: #b7ddcf;
  color: #146d5a;
  background: #effaf6;
}

.notice-error {
  border-color: #efc6c9;
  color: #a53f48;
  background: #fff5f5;
}

@keyframes notice-in {
  from { transform: translateY(-8px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-overlay {
  position: fixed;
  z-index: 40;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  background: rgba(23, 33, 43, .38);
}

.detail-drawer,
.form-modal {
  height: 100%;
  overflow: auto;
  background: #fff;
  box-shadow: -12px 0 35px rgba(17, 28, 35, .15);
  animation: slide-in .22s ease-out;
}

.detail-drawer {
  width: min(520px, 100%);
}

.form-modal {
  width: min(720px, 100%);
}

@keyframes slide-in {
  from { transform: translateX(20px); opacity: .5; }
  to { transform: translateX(0); opacity: 1; }
}

.modal-header {
  min-height: 82px;
  padding: 20px 26px;
  border-bottom: 1px solid var(--line);
}

.modal-header h2 {
  margin-bottom: 0;
  font-size: 20px;
}

.close-button {
  width: 34px;
  height: 34px;
  border-radius: 5px;
  font-size: 25px;
  line-height: 1;
}

.close-button:hover {
  color: #a53f48;
  background: #fff2f2;
}

.detail-body {
  padding: 24px 26px 35px;
}

.detail-code-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 22px;
}

.detail-code {
  color: #63727d;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px;
}

.detail-section {
  padding: 21px 0;
  border-top: 1px solid #edf0f2;
}

.detail-section h3,
.form-section h3 {
  margin-bottom: 15px;
  color: #53616c;
  font-size: 12px;
  letter-spacing: .04em;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin: 0;
}

.detail-grid > div {
  min-width: 0;
}

.detail-grid .detail-wide {
  grid-column: 1 / -1;
}

.detail-grid dt {
  margin-bottom: 5px;
  color: #9aa5ae;
  font-size: 11px;
}

.detail-grid dd {
  overflow-wrap: anywhere;
  color: #33424d;
  font-size: 13px;
}

.detail-remark {
  margin: 0;
  color: #586772;
  font-size: 13px;
  line-height: 1.65;
  white-space: pre-wrap;
}

.detail-meta {
  margin-bottom: 0;
  color: #a0aab1;
  font-size: 11px;
}

.detail-footer {
  padding: 15px 26px;
  border-top: 1px solid var(--line);
}

.supplier-form {
  padding: 23px 26px 25px;
}

.form-section {
  padding-bottom: 23px;
  margin-bottom: 23px;
  border-bottom: 1px solid #edf0f2;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 17px 16px;
}

.full-field {
  grid-column: 1 / -1;
}

.form-field {
  position: relative;
}

.form-field span {
  color: #53616c;
}

.form-field em {
  color: #c14d55;
  font-style: normal;
}

.form-field small {
  margin-top: -3px;
  color: #b34850;
  font-size: 11px;
  font-weight: 400;
}

.form-field input.invalid {
  border-color: #da7a80;
  background: #fffafa;
}

.form-actions {
  justify-content: flex-end;
}

.button-loader {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1120px) {
  .filter-grid {
    grid-template-columns: repeat(3, minmax(150px, 1fr));
  }

  .filter-actions {
    grid-column: auto;
  }
}

@media (max-width: 700px) {
  .supplier-page {
    padding: 20px 14px 30px;
  }

  h1 {
    font-size: 26px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-panel {
    padding: 16px;
  }

  .filter-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .filter-actions,
  .full-field {
    grid-column: auto;
  }

  .filter-actions {
    align-items: stretch;
  }

  .filter-actions .btn {
    flex: 1;
  }

  .table-toolbar,
  .table-footer {
    align-items: flex-start;
    flex-direction: column;
    padding: 16px;
  }

  .table-footer {
    gap: 12px;
  }

  .pagination-controls {
    width: 100%;
    justify-content: space-between;
  }

  .pagination-controls label {
    flex: 1;
  }

  .pagination-controls select {
    max-width: 100%;
  }

  .modal-header,
  .detail-body,
  .detail-footer,
  .supplier-form {
    padding-left: 18px;
    padding-right: 18px;
  }

  .detail-grid {
    gap: 14px 10px;
  }
}
</style>
