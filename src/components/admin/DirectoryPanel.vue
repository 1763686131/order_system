<template>
  <div
    ref="directoryRef"
    class="directory-menu"
    @keydown.esc="closeDirectory"
  >
    <button
      class="icon-btn directory-trigger"
      type="button"
      title="通讯录"
      aria-label="打开通讯录"
      aria-controls="employee-directory-panel"
      :aria-expanded="directoryOpen"
      @click.stop="toggleDirectory"
    >
      <svg class="icon-svg directory-trigger-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 3h11a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>
        <path d="M5 8H3M5 12H3M5 16H3"/>
        <circle cx="13" cy="9" r="2.2"/>
        <path d="M9.5 17c.5-2.1 1.7-3.2 3.5-3.2s3 1.1 3.5 3.2"/>
      </svg>
    </button>

    <Transition name="directory-panel">
      <section
        v-if="directoryOpen"
        id="employee-directory-panel"
        class="directory-panel"
        aria-label="员工通讯录"
      >
        <label class="directory-search">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="6.5"/>
            <path d="m16 16 4.5 4.5"/>
          </svg>
          <input
            v-model.trim="directorySearch"
            type="search"
            placeholder="搜索姓名、电话或职位"
            autocomplete="off"
          >
        </label>

        <div class="directory-content">
          <div v-if="directoryLoading && !directoryEmployees.length" class="directory-loading">
            <span v-for="index in 5" :key="index" class="directory-skeleton"></span>
          </div>

          <div v-else-if="directoryError" class="directory-state">
            <strong>通讯录加载失败</strong>
            <span>{{ directoryError }}</span>
            <button type="button" @click="loadDirectory">重新加载</button>
          </div>

          <div v-else-if="!directoryGroups.length" class="directory-state">
            <strong>{{ directorySearch ? '未找到匹配员工' : '暂无通讯录数据' }}</strong>
            <span>{{ directorySearch ? '请尝试其他姓名、电话或职位。' : '请先维护部门和员工档案。' }}</span>
          </div>

          <div v-else class="directory-departments">
            <section
              v-for="group in directoryGroups"
              :key="group.id"
              class="directory-department"
            >
              <button
                class="directory-department-toggle"
                type="button"
                :aria-expanded="isDirectoryDepartmentExpanded(group.id)"
                @click="toggleDirectoryDepartment(group.id)"
              >
                <svg
                  :class="{ expanded: isDirectoryDepartmentExpanded(group.id) }"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="m9 7 5 5-5 5"/>
                </svg>
                <span>{{ group.name }}</span>
                <small>{{ group.employees.length }}</small>
              </button>

              <div
                v-show="isDirectoryDepartmentExpanded(group.id)"
                class="directory-employee-list"
              >
                <article
                  v-for="employee in group.employees"
                  :key="`${group.id}-${employee.id}`"
                  class="directory-employee"
                  tabindex="0"
                  title="双击打开留言"
                  @dblclick.stop="openEmployeeChat(employee)"
                  @keydown.enter="openEmployeeChat(employee)"
                >
                  <div class="directory-avatar" aria-hidden="true">
                    <span>{{ employeeInitials(employee) }}</span>
                    <img
                      v-if="employee.avatarUrl"
                      :src="employee.avatarUrl"
                      alt=""
                      @error="hideBrokenDirectoryAvatar"
                    >
                  </div>

                  <div class="directory-employee-main">
                    <strong>{{ employee.displayName }}</strong>
                    <span>{{ employee.position || '暂无职位' }}</span>
                  </div>

                  <span class="directory-employee-phone">
                    {{ employee.phone || '暂无电话' }}
                  </span>

                  <span
                    :class="['directory-presence', { online: employee.online }]"
                    :title="employeePresenceTitle(employee)"
                  >
                    <i></i>{{ employee.online ? '在线' : '离线' }}
                  </span>
                </article>

                <div v-if="!group.employees.length" class="directory-department-empty">
                  暂无员工
                </div>
              </div>
            </section>
          </div>
        </div>

        <footer v-if="!directoryLoading && !directoryError" class="directory-footer">
          <span>{{ directoryEmployees.length }} 名员工</span>
          <span><i></i>{{ directoryOnlineCount }} 人在线</span>
        </footer>
      </section>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import request from '@/api/request'

const emit = defineEmits(['open-change', 'open-chat'])

const directoryRef = ref(null)
const directoryOpen = ref(false)
const directoryLoading = ref(false)
const directoryError = ref('')
const directorySearch = ref('')
const directoryDepartments = ref([])
const directoryEmployees = ref([])
const expandedDirectoryDepartments = ref([])

const UNASSIGNED_DEPARTMENT_ID = 'unassigned'

const directoryGroups = computed(() => {
  const keyword = directorySearch.value.trim().toLocaleLowerCase('zh-CN')
  const groups = directoryDepartments.value.map(department => ({
    id: department.id,
    name: department.name,
    employees: directoryEmployees.value.filter(employee =>
      employee.departmentIds.includes(department.id)
    )
  }))
  const unassignedEmployees = directoryEmployees.value.filter(
    employee => employee.departmentIds.length === 0
  )

  if (unassignedEmployees.length) {
    groups.push({
      id: UNASSIGNED_DEPARTMENT_ID,
      name: '未分配部门',
      employees: unassignedEmployees
    })
  }

  return groups
    .map(group => {
      const groupMatches = keyword && group.name.toLocaleLowerCase('zh-CN').includes(keyword)
      const employees = groupMatches
        ? group.employees
        : group.employees.filter(employee => {
            const searchableText = [
              employee.displayName,
              employee.phone,
              employee.position
            ].join(' ').toLocaleLowerCase('zh-CN')
            return !keyword || searchableText.includes(keyword)
          })

      return {
        ...group,
        employees: [...employees].sort((left, right) => {
          const presenceDifference = Number(right.online) - Number(left.online)
          if (presenceDifference) return presenceDifference
          return left.displayName.localeCompare(right.displayName, 'zh-CN')
        })
      }
    })
    .filter(group => !keyword || group.employees.length > 0)
})

const directoryOnlineCount = computed(() => {
  return directoryEmployees.value.filter(employee => employee.online).length
})

const closeDirectory = () => {
  directoryOpen.value = false
  directorySearch.value = ''
  expandedDirectoryDepartments.value = []
  emit('open-change', false)
}

const loadDirectory = async () => {
  directoryLoading.value = true
  directoryError.value = ''
  try {
    const response = await request.get('/admin/directory')
    directoryDepartments.value = Array.isArray(response?.departments)
      ? response.departments
      : []
    directoryEmployees.value = Array.isArray(response?.employees)
      ? response.employees.map(employee => ({
          ...employee,
          departmentIds: Array.isArray(employee.departmentIds)
            ? employee.departmentIds.map(Number).filter(Boolean)
            : [],
          online: Boolean(employee.online)
        }))
      : []
  } catch (error) {
    directoryError.value = error?.response?.data?.message || '请稍后重试'
  } finally {
    directoryLoading.value = false
  }
}

const toggleDirectory = () => {
  if (directoryOpen.value) {
    closeDirectory()
    return
  }
  directoryOpen.value = true
  emit('open-change', true)
  loadDirectory()
}

const toggleDirectoryDepartment = departmentId => {
  if (directorySearch.value) return
  expandedDirectoryDepartments.value = expandedDirectoryDepartments.value.includes(departmentId)
    ? expandedDirectoryDepartments.value.filter(id => id !== departmentId)
    : [...expandedDirectoryDepartments.value, departmentId]
}

const isDirectoryDepartmentExpanded = departmentId => {
  return Boolean(directorySearch.value) ||
    expandedDirectoryDepartments.value.includes(departmentId)
}

const employeeInitials = employee => {
  const name = String(employee?.displayName || '').trim()
  return name ? name.slice(-2) : '员工'
}

const hideBrokenDirectoryAvatar = event => {
  event.currentTarget.style.display = 'none'
}

const employeePresenceTitle = employee => {
  if (employee.online) return '最近 10 分钟内有活动'
  if (employee.lastActiveAt) return `最近活跃：${employee.lastActiveAt}`
  return '暂无登录活动'
}

const openEmployeeChat = employee => {
  emit('open-chat', {
    id: employee.id,
    displayName: employee.displayName || '员工',
    phone: employee.phone || '',
    position: employee.position || '',
    avatarUrl: employee.avatarUrl || '',
    online: Boolean(employee.online)
  })
}

const handleDirectoryClickOutside = event => {
  if (!directoryRef.value?.contains(event.target)) {
    closeDirectory()
  }
}

defineExpose({
  close: closeDirectory,
  reload: loadDirectory
})

onMounted(() => {
  document.addEventListener('pointerdown', handleDirectoryClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleDirectoryClickOutside)
})
</script>

<style scoped>
.directory-menu {
  position: relative;
  z-index: 40;
  flex: 0 0 auto;
}

.icon-btn {
  position: relative;
  display: flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.icon-btn:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.icon-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.icon-svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.directory-trigger[aria-expanded="true"] {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.directory-trigger-icon {
  width: 19px;
  height: 19px;
}

.directory-panel {
  position: absolute;
  z-index: 2200;
  top: calc(100% + 8px);
  right: 0;
  width: 400px;
  max-width: calc(100vw - 24px);
  overflow: hidden;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
}

.directory-search {
  position: relative;
  display: block;
  margin: 14px;
}

.directory-search svg {
  position: absolute;
  top: 10px;
  left: 11px;
  width: 18px;
  height: 18px;
  color: var(--text-muted);
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  pointer-events: none;
}

.directory-search input {
  width: 100%;
  height: 38px;
  padding: 0 11px 0 36px;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
  font: inherit;
  font-size: 13px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.directory-search input::placeholder {
  color: var(--text-muted);
}

.directory-search input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.directory-content {
  max-height: min(500px, calc(100vh - 160px));
  overflow-y: auto;
  border-top: 1px solid var(--border);
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}

.directory-content::-webkit-scrollbar {
  width: 7px;
}

.directory-content::-webkit-scrollbar-track {
  background: transparent;
}

.directory-content::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 999px;
}

.directory-loading {
  display: grid;
  gap: 8px;
  padding: 14px;
}

.directory-skeleton {
  display: block;
  height: 54px;
  overflow: hidden;
  border-radius: 5px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e7edf2 45%, #f1f5f9 65%);
  background-size: 240% 100%;
  animation: directoryShimmer 1.25s linear infinite;
}

@keyframes directoryShimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}

.directory-state {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  padding: 20px;
  color: var(--text-muted);
  text-align: center;
}

.directory-state strong {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 650;
}

.directory-state span {
  max-width: 280px;
  font-size: 12px;
  line-height: 1.5;
}

.directory-state button {
  height: 34px;
  margin-top: 6px;
  padding: 0 12px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.directory-state button:hover {
  background: #ddf3eb;
}

.directory-state button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.directory-department {
  border-bottom: 1px solid var(--border);
}

.directory-department:last-child {
  border-bottom: 0;
}

.directory-department-toggle {
  display: grid;
  width: 100%;
  min-height: 44px;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  color: var(--text);
  background: var(--panel-bg);
  border: 0;
  cursor: pointer;
  text-align: left;
  transition: background 0.18s ease, color 0.18s ease;
}

.directory-department-toggle:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.directory-department-toggle:focus-visible {
  position: relative;
  z-index: 1;
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.directory-department-toggle svg {
  width: 17px;
  height: 17px;
  color: var(--text-muted);
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
  transition: transform 0.18s ease;
}

.directory-department-toggle svg.expanded {
  transform: rotate(90deg);
}

.directory-department-toggle span {
  overflow: hidden;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.directory-department-toggle small {
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  color: var(--text-secondary);
  background: #f1f5f9;
  border-radius: 999px;
  box-sizing: border-box;
  font-size: 11px;
  font-weight: 700;
  line-height: 22px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.directory-employee-list {
  background: #f8fafc;
  border-top: 1px solid var(--border);
}

.directory-employee {
  display: grid;
  min-height: 64px;
  grid-template-columns: 38px minmax(80px, 1fr) minmax(88px, auto) auto;
  align-items: center;
  gap: 10px;
  padding: 9px 14px 9px 40px;
  border-bottom: 1px solid #edf1f5;
  cursor: pointer;
  outline: none;
  transition: background 0.18s ease;
}

.directory-employee:last-child {
  border-bottom: 0;
}

.directory-employee:hover,
.directory-employee:focus-visible {
  background: var(--accent-soft);
}

.directory-employee:focus-visible {
  box-shadow: inset 0 0 0 2px var(--accent);
}

.directory-avatar {
  position: relative;
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  place-items: center;
  overflow: hidden;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 50%;
  box-sizing: border-box;
  font-size: 12px;
  font-weight: 700;
}

.directory-avatar img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.directory-employee-main {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 6px;
}

.directory-employee-main strong {
  flex: 0 1 auto;
  overflow: hidden;
  color: var(--text);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.directory-employee-main span {
  flex: 0 1 auto;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 500;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.directory-employee-phone {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  line-height: 1.4;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.directory-presence {
  display: inline-flex;
  min-height: 23px;
  flex: 0 0 auto;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  color: var(--text-secondary);
  background: #f1f2f4;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
}

.directory-presence i {
  width: 6px;
  height: 6px;
  background: var(--text-muted);
  border-radius: 50%;
}

.directory-presence.online {
  color: #13734f;
  background: #eaf8f1;
}

.directory-presence.online i {
  background: var(--accent);
}

.directory-department-empty {
  padding: 16px 14px 16px 40px;
  color: var(--text-muted);
  font-size: 12px;
}

.directory-footer {
  display: flex;
  min-height: 42px;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  color: var(--text-secondary);
  background: var(--panel-bg);
  border-top: 1px solid var(--border);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.directory-footer span:last-child {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.directory-footer i {
  width: 7px;
  height: 7px;
  background: var(--accent);
  border-radius: 50%;
}

.directory-panel-enter-active,
.directory-panel-leave-active {
  transform-origin: top right;
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.directory-panel-enter-from,
.directory-panel-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 780px) {
  .directory-panel {
    position: fixed;
    top: 64px;
    right: 12px;
    width: calc(100vw - 24px);
  }

  .directory-content {
    max-height: calc(100vh - 174px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .directory-panel-enter-active,
  .directory-panel-leave-active {
    transition: none;
  }

  .directory-skeleton {
    animation: none;
  }
}
</style>
