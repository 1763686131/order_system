<template>
  <div class="page-root department-page">
    <section class="department-workspace">
      <aside class="department-panel">
        <div class="panel-header">
          <div>
            <h2>部门配置</h2>
            <span>{{ departments.length }} 个部门 · {{ totalEmployeeCount }} 名员工</span>
          </div>
          <div class="department-header-actions">
            <button
              v-if="selectedDepartment"
              class="icon-button"
              type="button"
              title="编辑当前部门"
              aria-label="编辑当前部门"
              @click="openEdit(selectedDepartment)"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m4 16.5-.8 3.3 3.3-.8L18 7.5 15.5 5 4 16.5Z"></path>
                <path d="m14.5 6 2.5 2.5"></path>
              </svg>
            </button>
            <button
              class="icon-button"
              type="button"
              title="新增部门"
              aria-label="新增部门"
              @click="openCreate"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14"></path>
                <path d="M5 12h14"></path>
              </svg>
            </button>
          </div>
        </div>

        <div class="department-list">
          <button
            class="department-item virtual-item"
            :class="{ selected: selectedDepartmentId === ALL_ID }"
            type="button"
            @click="selectVirtualDepartment(ALL_ID)"
          >
            <span class="department-icon neutral">全</span>
            <span class="department-copy">
              <strong>全部员工</strong>
              <small>查看所有员工</small>
            </span>
            <span class="department-count">{{ employees.length }}</span>
          </button>

          <button
            v-for="department in departments"
            :key="department.id"
            class="department-item"
            :class="{ selected: department.id === selectedDepartmentId }"
            type="button"
            @click="selectDepartment(department)"
          >
            <span :class="['department-icon', toneForDepartment(department.id)]">
              {{ department.name.slice(0, 1) }}
            </span>
            <span class="department-copy">
              <strong>{{ department.name }}</strong>
              <small>{{ department.status === 'active' ? '启用中' : '已停用' }}</small>
            </span>
            <span class="department-count">{{ department.employeeCount }}</span>
          </button>

          <button
            class="department-item virtual-item"
            :class="{ selected: selectedDepartmentId === UNASSIGNED_ID }"
            type="button"
            @click="selectVirtualDepartment(UNASSIGNED_ID)"
          >
            <span class="department-icon warning">未</span>
            <span class="department-copy">
              <strong>未分配部门</strong>
              <small>需要补充归属</small>
            </span>
            <span class="department-count">{{ unassignedEmployeeCount }}</span>
          </button>
        </div>

      </aside>

      <section class="employee-panel">
        <div class="panel-header employee-panel-header">
          <div>
            <h2>{{ employeePanelTitle }}</h2>
            <span>{{ employeePanelHint }}</span>
          </div>
          <div class="employee-panel-actions">
            <label class="search-box">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5"></circle>
                <path d="m16 16 4 4"></path>
              </svg>
              <input v-model.trim="employeeSearch" type="search" placeholder="搜索员工" />
            </label>
            <button
              v-if="selectedDepartment"
              class="button button-primary"
              type="button"
              :disabled="selectedDepartment.status !== 'active'"
              :title="selectedDepartment.status !== 'active' ? '停用部门不能添加员工' : '添加员工'"
              @click="openAddEmployee"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14"></path>
                <path d="M5 12h14"></path>
              </svg>
              添加员工
            </button>
            <button class="button button-secondary" type="button" @click="goToEmployees">
              员工管理
            </button>
          </div>
        </div>

        <div class="employee-list-wrap">
          <table class="employee-table">
            <thead>
              <tr>
                <th>员工信息</th>
                <th>工号</th>
                <th>职位</th>
                <th>联系电话</th>
                <th>账号状态</th>
                <th>在职状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="employee in filteredEmployees" :key="employee.id">
                <td>
                  <div class="employee-cell">
                    <span class="avatar" :style="avatarStyle(employee)">{{ employee.displayName.slice(0, 1) }}</span>
                    <div>
                      <strong>{{ employee.displayName }}</strong>
                      <small>{{ employee.department || '未分配部门' }}</small>
                    </div>
                  </div>
                </td>
                <td class="tabular">{{ employee.employeeNo }}</td>
                <td>{{ employee.position || '暂无职位' }}</td>
                <td class="tabular">{{ employee.phone || '—' }}</td>
                <td>
                  <span :class="['status-badge', employee.accountStatus]">
                    {{ accountStatusLabel(employee.accountStatus) }}
                  </span>
                </td>
                <td>
                  <span :class="['status-badge', employee.employmentStatus]">
                    {{ employmentStatusLabel(employee.employmentStatus) }}
                  </span>
                </td>
              </tr>
              <tr v-if="filteredEmployees.length === 0">
                <td colspan="6">
                  <div class="empty-state">
                    <strong>暂无匹配员工</strong>
                    <span>调整部门或搜索条件后再试</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </section>

    <Teleport to="body">
      <div v-if="departmentModalVisible" class="modal-layer" @click.self="closeDepartmentModal">
        <section class="department-modal" role="dialog" aria-modal="true" aria-labelledby="department-modal-title">
          <div class="modal-header">
            <div>
              <span class="modal-eyebrow">{{ editingDepartment ? '编辑部门' : '新增部门' }}</span>
              <h2 id="department-modal-title">{{ editingDepartment ? '部门信息' : '新建部门' }}</h2>
            </div>
            <button class="icon-button" type="button" title="关闭" :disabled="saving" @click="closeDepartmentModal">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12"></path>
                <path d="m18 6-12 12"></path>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <label class="field">
              <span>部门名称 <em>*</em></span>
              <input v-model.trim="departmentDraft.name" type="text" placeholder="例如 销售部" />
            </label>
            <label class="field">
              <span>状态</span>
              <select v-model="departmentDraft.status">
                <option value="active">启用</option>
                <option value="disabled">停用</option>
              </select>
            </label>
            <label class="field">
              <span>排序</span>
              <input v-model.number="departmentDraft.sortOrder" type="number" min="0" step="1" />
            </label>
            <p class="modal-hint">
              有员工归属的部门不能停用或删除，请先到员工管理调整员工部门。
            </p>
          </div>

          <div class="modal-footer">
            <button
              v-if="editingDepartment && departmentDraft.employeeCount === 0"
              class="button button-danger"
              type="button"
              :disabled="saving"
              @click="deleteDepartment"
            >
              删除部门
            </button>
            <span v-else></span>
            <div class="modal-footer-actions">
              <button class="button button-secondary" type="button" :disabled="saving" @click="closeDepartmentModal">
                取消
              </button>
              <button class="button button-primary" type="button" :disabled="saving" @click="saveDepartment">
                {{ saving ? '保存中...' : '保存部门' }}
              </button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="employeeModalVisible && selectedDepartment" class="modal-layer" @click.self="closeAddEmployee">
        <section class="employee-picker-modal" role="dialog" aria-modal="true" aria-labelledby="employee-picker-title">
          <div class="modal-header">
            <div>
              <span class="modal-eyebrow">添加员工</span>
              <h2 id="employee-picker-title">加入{{ selectedDepartment.name }}</h2>
            </div>
            <button class="icon-button" type="button" title="关闭" :disabled="saving" @click="closeAddEmployee">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12"></path>
                <path d="m18 6-12 12"></path>
              </svg>
            </button>
          </div>

          <div class="picker-toolbar">
            <label class="picker-search">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5"></circle>
                <path d="m16 16 4 4"></path>
              </svg>
              <input v-model.trim="employeePickerQuery" type="search" placeholder="搜索姓名、工号或手机号" />
            </label>
            <span>已选择 {{ employeePickerSelectedIds.length }} 人</span>
          </div>

          <div class="employee-picker-body">
            <label
              v-for="employee in availableEmployees"
              :key="employee.id"
              class="employee-picker-option"
              :class="{ selected: employeePickerSelectedIds.includes(employee.id) }"
            >
              <input v-model="employeePickerSelectedIds" type="checkbox" :value="employee.id" />
              <span class="avatar" :style="avatarStyle(employee)">{{ employee.displayName.slice(0, 1) }}</span>
              <span class="employee-picker-copy">
                <strong>{{ employee.displayName }}</strong>
                <small>{{ employee.employeeNo }} · {{ employee.department || '未分配部门' }} · {{ employee.phone || '暂无电话' }}</small>
              </span>
              <span v-if="employee.departmentId" class="employee-picker-move-hint">调整部门</span>
            </label>
            <div v-if="availableEmployees.length === 0" class="picker-empty">
              <strong>{{ employeePickerQuery ? '没有找到匹配员工' : '暂无可添加员工' }}</strong>
              <span>{{ employeePickerQuery ? '请调整搜索条件后重试' : '当前部门外暂无其他员工' }}</span>
            </div>
          </div>

          <div class="modal-footer">
            <span class="picker-hint">选择其他部门员工会将其调整到当前部门</span>
            <div class="modal-footer-actions">
              <button class="button button-secondary" type="button" :disabled="saving" @click="closeAddEmployee">
                取消
              </button>
              <button
                class="button button-primary"
                type="button"
                :disabled="saving || employeePickerSelectedIds.length === 0"
                @click="addSelectedEmployees"
              >
                {{ saving ? '添加中...' : '确认添加' }}
              </button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>

    <transition name="notice">
      <div v-if="notice" class="page-notice" role="status">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9"></circle>
          <path d="m8 12 2.5 2.5L16 9"></path>
        </svg>
        <span>{{ notice }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()
const ALL_ID = 'all'
const UNASSIGNED_ID = 'unassigned'

const departments = ref([])
const employees = ref([])
const selectedDepartmentId = ref(null)
const employeeSearch = ref('')
const editingDepartment = ref(false)
const departmentModalVisible = ref(false)
const departmentModalReturnId = ref(null)
const employeeModalVisible = ref(false)
const employeePickerQuery = ref('')
const employeePickerSelectedIds = ref([])
const departmentDraft = ref(createEmptyDepartment())
const saving = ref(false)
const notice = ref('')
let noticeTimer

const selectedDepartment = computed(() =>
  departments.value.find(item => item.id === selectedDepartmentId.value) || null
)

const totalEmployeeCount = computed(() => employees.value.length)
const unassignedEmployeeCount = computed(() =>
  employees.value.filter(employee => !employee.departmentId).length
)

const employeePanelTitle = computed(() => {
  if (selectedDepartmentId.value === ALL_ID) return '全部员工'
  if (selectedDepartmentId.value === UNASSIGNED_ID) return '未分配部门'
  return selectedDepartment.value?.name || '员工列表'
})

const employeePanelHint = computed(() => {
  if (selectedDepartmentId.value === ALL_ID) return `共 ${employees.value.length} 人`
  if (selectedDepartmentId.value === UNASSIGNED_ID) return '需要补充部门归属的员工'
  return `${selectedDepartment.value?.status === 'active' ? '启用中' : '已停用'} · 共 ${selectedDepartment.value?.employeeCount || 0} 人`
})

const departmentEmployees = computed(() => {
  if (selectedDepartmentId.value === ALL_ID) return employees.value
  if (selectedDepartmentId.value === UNASSIGNED_ID) {
    return employees.value.filter(employee => !employee.departmentId)
  }
  return employees.value.filter(employee => employee.departmentId === selectedDepartmentId.value)
})

const filteredEmployees = computed(() => {
  const keyword = employeeSearch.value.toLowerCase()
  if (!keyword) return departmentEmployees.value
  return departmentEmployees.value.filter(employee =>
    [employee.displayName, employee.employeeNo, employee.username, employee.phone, employee.position]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  )
})

const availableEmployees = computed(() => {
  if (!selectedDepartment.value) return []
  const keyword = employeePickerQuery.value.toLowerCase()
  return employees.value.filter(employee => {
    if (employee.departmentId === selectedDepartment.value.id) return false
    if (!keyword) return true
    return [employee.displayName, employee.employeeNo, employee.phone, employee.department]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  })
})

function createEmptyDepartment() {
  return {
    id: null,
    name: '',
    status: 'active',
    sortOrder: 0,
    employeeCount: 0
  }
}

async function loadData(preferredId = selectedDepartmentId.value) {
  try {
    const [departmentResponse, employeeResponse] = await Promise.all([
      request.get('/admin/departments'),
      request.get('/admin/employees')
    ])
    departments.value = Array.isArray(departmentResponse.departments)
      ? departmentResponse.departments
      : []
    employees.value = Array.isArray(employeeResponse.employees)
      ? employeeResponse.employees
      : []

    const preferredExists = departments.value.some(item => item.id === preferredId)
    if (preferredId === ALL_ID || preferredId === UNASSIGNED_ID || preferredExists) {
      selectedDepartmentId.value = preferredId
    } else {
      selectedDepartmentId.value = departments.value[0]?.id || ALL_ID
    }
  } catch (error) {
    showNotice(error?.response?.data?.message || '部门数据加载失败')
  }
}

function selectDepartment(department) {
  selectedDepartmentId.value = department.id
  employeeSearch.value = ''
}

function selectVirtualDepartment(id) {
  selectedDepartmentId.value = id
  employeeSearch.value = ''
}

function openEdit(department) {
  if (!department) return
  departmentModalReturnId.value = department.id
  editingDepartment.value = true
  departmentDraft.value = { ...department }
  departmentModalVisible.value = true
}

function openCreate() {
  departmentModalReturnId.value = selectedDepartmentId.value
  selectedDepartmentId.value = null
  departmentDraft.value = {
    ...createEmptyDepartment(),
    sortOrder: departments.value.length
  }
  editingDepartment.value = true
  departmentModalVisible.value = true
}

function closeDepartmentModal() {
  if (saving.value) return
  if (!editingDepartment.value || !departmentDraft.value.id) {
    selectedDepartmentId.value = departmentModalReturnId.value || departments.value[0]?.id || ALL_ID
  }
  departmentModalVisible.value = false
  editingDepartment.value = false
  departmentModalReturnId.value = null
  departmentDraft.value = createEmptyDepartment()
}

async function saveDepartment() {
  if (!departmentDraft.value.name) {
    showNotice('请先填写部门名称')
    return
  }
  try {
    saving.value = true
    const payload = {
      name: departmentDraft.value.name,
      status: departmentDraft.value.status,
      sortOrder: Number(departmentDraft.value.sortOrder) || 0
    }
    const response = departmentDraft.value.id
      ? await request.put(`/admin/departments/${departmentDraft.value.id}`, payload)
      : await request.post('/admin/departments', payload)
    showNotice(response.message || '部门已保存')
    const nextDepartmentId = response.department?.id || departmentDraft.value.id
    departmentModalVisible.value = false
    editingDepartment.value = false
    departmentModalReturnId.value = null
    await loadData(nextDepartmentId)
  } catch (error) {
    showNotice(error?.response?.data?.message || '部门保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteDepartment() {
  if (!departmentDraft.value.id || departmentDraft.value.employeeCount > 0) return
  if (!window.confirm(`确认删除部门“${departmentDraft.value.name}”吗？`)) return
  try {
    saving.value = true
    const response = await request.delete(`/admin/departments/${departmentDraft.value.id}`)
    showNotice(response.message || '部门已删除')
    departmentModalVisible.value = false
    editingDepartment.value = false
    departmentModalReturnId.value = null
    await loadData(ALL_ID)
  } catch (error) {
    showNotice(error?.response?.data?.message || '部门删除失败')
  } finally {
    saving.value = false
  }
}

function openAddEmployee() {
  if (!selectedDepartment.value || selectedDepartment.value.status !== 'active') return
  employeePickerQuery.value = ''
  employeePickerSelectedIds.value = []
  employeeModalVisible.value = true
}

function closeAddEmployee() {
  if (saving.value) return
  employeeModalVisible.value = false
  employeePickerQuery.value = ''
  employeePickerSelectedIds.value = []
}

function employeeUpdatePayload(employee, departmentId) {
  return {
    ...employee,
    departmentId,
    password: '',
    passwordConfirm: '',
    roleIds: Array.isArray(employee.roleIds) ? [...employee.roleIds] : []
  }
}

async function addSelectedEmployees() {
  if (!selectedDepartment.value || employeePickerSelectedIds.value.length === 0) return
  const targetDepartmentId = selectedDepartment.value.id
  const selectedEmployees = employees.value.filter(employee =>
    employeePickerSelectedIds.value.includes(employee.id)
  )
  try {
    saving.value = true
    let addedCount = 0
    for (const employee of selectedEmployees) {
      const response = await request.put(
        `/admin/employees/${employee.id}`,
        employeeUpdatePayload(employee, targetDepartmentId)
      )
      const index = employees.value.findIndex(item => item.id === employee.id)
      if (index !== -1 && response.employee) employees.value[index] = response.employee
      addedCount += 1
    }
    showNotice(`已添加 ${addedCount} 名员工到${selectedDepartment.value.name}`)
    employeeModalVisible.value = false
    employeePickerQuery.value = ''
    employeePickerSelectedIds.value = []
    await loadData(targetDepartmentId)
  } catch (error) {
    showNotice(error?.response?.data?.message || '员工添加失败，已完成的绑定已保留')
  } finally {
    saving.value = false
  }
}

function goToEmployees() {
  router.push('/admin/hr/employees')
}

function toneForDepartment(id) {
  return ['green', 'blue', 'orange', 'purple', 'red'][Math.max(0, Number(id) - 1) % 5]
}

function avatarStyle(employee) {
  const style = {
    backgroundColor: employee.avatarColor || '#e9f8f3',
    color: '#275a4d'
  }
  if (employee.avatarUrl) {
    style.backgroundImage = `url("${employee.avatarUrl}")`
    style.backgroundPosition = 'center'
    style.backgroundRepeat = 'no-repeat'
    style.backgroundSize = 'cover'
    style.color = 'transparent'
  }
  return style
}

function accountStatusLabel(status) {
  return { active: '正常', disabled: '已停用', pending: '待开通' }[status] || '待开通'
}

function employmentStatusLabel(status) {
  return { active: '在职', probation: '试用期', leave: '休假', resigned: '离职' }[status] || '未知'
}

function showNotice(message) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, 3000)
}

onMounted(() => loadData())
</script>

<style scoped>
.page-root {
  --accent: #0f9f78;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #fff;
  --border: #dfe5ec;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  min-height: 100%;
  padding: 0;
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
  box-sizing: border-box;
}

.department-workspace {
  display: grid;
  grid-template-columns: minmax(300px, 0.78fr) minmax(620px, 1.7fr);
  gap: 14px;
}

.department-panel,
.employee-panel {
  min-width: 0;
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
}

.panel-header {
  display: flex;
  min-height: 70px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 16px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.panel-header h2 {
  font-size: 15px;
}

.panel-header > div > span {
  display: block;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.department-header-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  flex: 0 0 36px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.icon-button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.icon-button svg,
.page-notice svg,
.search-box svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.department-list {
  padding: 8px;
}

.department-item {
  display: flex;
  width: 100%;
  min-height: 66px;
  align-items: center;
  gap: 10px;
  padding: 10px;
  color: var(--text);
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.department-item:hover {
  background: #f8fafc;
  border-color: var(--border);
}

.department-item.selected {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.department-icon {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  font-size: 14px;
  font-weight: 750;
}

.department-icon.green { color: #13734f; background: #eaf8f1; }
.department-icon.blue { color: #16647a; background: #e7f5f8; }
.department-icon.orange { color: #a4510b; background: #fff3df; }
.department-icon.purple { color: #6651a8; background: #f1edff; }
.department-icon.red { color: #b4232f; background: #fcebed; }
.department-icon.neutral { color: #596579; background: #f1f5f9; }
.department-icon.warning { color: #a4510b; background: #fff3df; }

.department-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.department-copy strong,
.department-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.department-copy strong { font-size: 13px; }
.department-copy small { color: var(--text-muted); font-size: 11px; }

.department-count {
  min-width: 24px;
  color: var(--text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.field {
  display: block;
  margin-top: 12px;
}

.field > span {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 650;
}

.field em { color: #b4232f; font-style: normal; }

.field input,
.field select,
.search-box input {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font: inherit;
  font-size: 13px;
  box-sizing: border-box;
}

.field input:focus,
.field select:focus,
.search-box input:focus {
  outline: 2px solid rgba(15, 159, 120, 0.14);
  border-color: var(--accent);
}

.employee-panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.button {
  display: inline-flex;
  height: 36px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 5px;
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
}

.button:disabled { opacity: 0.55; cursor: not-allowed; }
.button svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}
.button-primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.button-primary:hover:not(:disabled) { background: var(--accent-dark); border-color: var(--accent-dark); }
.button-secondary { color: var(--text-secondary); background: #fff; border-color: var(--border-strong); }
.button-secondary:hover { color: var(--accent-dark); background: var(--accent-soft); border-color: var(--accent-border); }
.button-danger { color: #b4232f; background: #fff; border-color: #efb4bc; }
.button-danger:hover:not(:disabled) { background: #fcebed; }

.modal-layer {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --panel-bg: #fff;
  --border: #dfe5ec;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  box-sizing: border-box;
}

.department-modal,
.employee-picker-modal {
  display: flex;
  width: min(520px, calc(100vw - 32px));
  max-height: min(680px, calc(100vh - 32px));
  flex-direction: column;
  color: var(--text);
  background: var(--panel-bg, #fff);
  border: 1px solid var(--border, #dfe5ec);
  border-radius: 7px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.22);
  overflow: hidden;
}

.employee-picker-modal {
  width: min(660px, calc(100vw - 32px));
}

.modal-header {
  display: flex;
  min-height: 78px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.modal-eyebrow {
  display: block;
  margin-bottom: 5px;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 650;
}

.modal-header h2 {
  font-size: 18px;
  line-height: 1.3;
}

.modal-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f8fafc;
}

.modal-body .field:first-child { margin-top: 0; }

.modal-hint {
  margin-top: 14px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.6;
}

.modal-footer {
  display: flex;
  min-height: 70px;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 20px;
  background: #fff;
  border-top: 1px solid var(--border);
  box-sizing: border-box;
}

.modal-footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.picker-toolbar {
  display: flex;
  min-height: 62px;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
}

.picker-toolbar > span {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.picker-search {
  display: flex;
  width: min(330px, 100%);
  height: 36px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  color: var(--text-muted);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
}

.picker-search:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.picker-search svg {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.picker-search input {
  width: 100%;
  min-width: 0;
  height: 100%;
  padding: 0;
  color: var(--text);
  background: transparent;
  border: 0;
  outline: 0;
  font: inherit;
  font-size: 12px;
}

.employee-picker-body {
  min-height: 180px;
  max-height: 390px;
  padding: 14px 20px;
  overflow-y: auto;
  background: #f4f7f9;
}

.employee-picker-option {
  display: flex;
  min-height: 62px;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  box-sizing: border-box;
  transition: border-color 0.18s ease, background 0.18s ease;
}

.employee-picker-option:last-child { margin-bottom: 0; }

.employee-picker-option:hover,
.employee-picker-option.selected {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.employee-picker-option input {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  accent-color: var(--accent);
}

.employee-picker-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.employee-picker-copy strong,
.employee-picker-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.employee-picker-copy strong { color: var(--text); font-size: 13px; }
.employee-picker-copy small { color: var(--text-muted); font-size: 11px; }

.employee-picker-move-hint {
  flex: 0 0 auto;
  color: #a4510b;
  font-size: 11px;
}

.picker-empty {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  color: var(--text-muted);
  text-align: center;
}

.picker-empty strong { color: var(--text-secondary); font-size: 13px; }
.picker-empty span,
.picker-hint { font-size: 11px; }
.picker-hint { color: var(--text-muted); }

.employee-panel-header { align-items: center; }

.search-box {
  position: relative;
  display: block;
  width: 190px;
}

.search-box svg {
  position: absolute;
  top: 9px;
  left: 10px;
  color: var(--text-muted);
  pointer-events: none;
}

.search-box input { padding-left: 32px; }

.employee-list-wrap { overflow-x: auto; }

.employee-table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
  table-layout: fixed;
}

.employee-table th {
  height: 44px;
  padding: 0 14px;
  color: var(--text-secondary);
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
}

.employee-table td {
  height: 68px;
  padding: 9px 14px;
  border-bottom: 1px solid #edf1f5;
  color: var(--text-secondary);
  font-size: 13px;
  vertical-align: middle;
}

.employee-table th:first-child { width: 190px; }
.employee-table th:nth-child(2) { width: 100px; }
.employee-table th:nth-child(3) { width: 140px; }
.employee-table th:nth-child(4) { width: 135px; }
.employee-table th:nth-child(5),
.employee-table th:nth-child(6) { width: 100px; }

.employee-cell {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}

.employee-cell > div { min-width: 0; }
.employee-cell strong,
.employee-cell small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.employee-cell strong { color: var(--text); font-size: 13px; }
.employee-cell small { margin-top: 4px; color: var(--text-muted); font-size: 11px; }

.avatar {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 750;
}

.status-badge {
  display: inline-flex;
  min-height: 23px;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
  box-sizing: border-box;
}

.status-badge.active { color: #13734f; background: #eaf8f1; }
.status-badge.disabled,
.status-badge.resigned { color: #7b8492; background: #f1f2f4; }
.status-badge.pending,
.status-badge.probation { color: #a4510b; background: #fff3df; }
.status-badge.leave { color: #16647a; background: #e7f5f8; }

.tabular { font-variant-numeric: tabular-nums; }

.empty-state {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  color: var(--text-muted);
}

.empty-state strong { color: var(--text-secondary); font-size: 13px; }
.empty-state span { font-size: 12px; }

.page-notice {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 2100;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  color: #13734f;
  background: #eaf8f1;
  border: 1px solid var(--accent-border);
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
  font-size: 12px;
  font-weight: 650;
}

.page-notice svg { width: 16px; height: 16px; }

.notice-enter-active,
.notice-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.notice-enter-from,
.notice-leave-to { opacity: 0; transform: translateY(6px); }

@media (max-width: 1100px) {
  .department-workspace { grid-template-columns: 1fr; }
  .department-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 680px) {
  .department-list { grid-template-columns: 1fr; }
  .employee-panel-header { align-items: flex-start; flex-direction: column; }
  .employee-panel-actions { width: 100%; flex-wrap: wrap; }
  .search-box { flex: 1; width: auto; }
  .modal-layer { padding: 12px; }
  .picker-toolbar { align-items: stretch; flex-direction: column; }
  .picker-search { width: 100%; }
  .picker-toolbar > span { align-self: flex-end; }
  .modal-footer { align-items: flex-end; flex-direction: column; }
  .modal-footer > span { align-self: flex-start; }
  .modal-footer-actions { width: 100%; justify-content: flex-end; }
  .page-notice { right: 14px; bottom: 14px; left: 14px; }
}
</style>
