<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="handleClose">
        <div class="modal-content modal-large">
          <div class="modal-close" @click="handleClose">×</div>

          <div class="modal-header">
            <div class="modal-title">系统账户与权限管理控制台</div>
          </div>

          <div class="modal-body">
            <div class="user-manage-container">
              <div class="user-list-panel">
                <div class="panel-header">
                  <strong>员工名单</strong>
                  <button class="btn-primary btn-sm" @click="prepareCreateUser">
                    + 新增员工
                  </button>
                </div>
                <div class="user-list">
                  <div
                    v-for="user in users"
                    :key="user.id"
                    class="user-item"
                    :class="{ active: selectedUser?.id === user.id }"
                    @click="selectUser(user)"
                  >
                    <div class="user-name">{{ user.name }}</div>
                    <div class="user-role">{{ getRoleName(user.role) }}</div>
                  </div>
                </div>
              </div>

              <div v-if="selectedUser" class="user-detail-panel">
                <h4>用户信息配置</h4>
                <!-- 用户详情表单 - 简化版 -->
                <div class="form-item">
                  <label>员工真实姓名：</label>
                  <input v-model="selectedUser.name" />
                </div>
                <div class="form-item">
                  <label>系统岗位级别：</label>
                  <select v-model="selectedUser.role">
                    <option value="employee">普通员工</option>
                    <option value="admin">管理员</option>
                  </select>
                </div>
                <!-- 更多表单项... -->
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-default" @click="handleClose">关闭</button>
            <button v-if="selectedUser" class="btn-primary" @click="saveUser">
              保存账户与权限
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { getUsers, createUser, updateUser } from '@/api/users'

const props = defineProps({
  visible: Boolean
})

const emit = defineEmits(['update:visible'])

const users = ref([])
const selectedUser = ref(null)

const getRoleName = (role) => {
  const roleMap = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'employee': '员工'
  }
  return roleMap[role] || role
}

const loadUsers = async () => {
  try {
    const res = await getUsers()
    if (res.success) {
      users.value = res.data || []
    }
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

const selectUser = (user) => {
  selectedUser.value = { ...user }
}

const prepareCreateUser = () => {
  selectedUser.value = {
    id: null,
    username: '',
    name: '',
    role: 'employee',
    permissions: []
  }
}

const saveUser = async () => {
  // 保存用户逻辑
  console.log('Save user:', selectedUser.value)
}

const handleClose = () => {
  emit('update:visible', false)
  selectedUser.value = null
}

watch(() => props.visible, (val) => {
  if (val) {
    loadUsers()
  }
})
</script>

<style scoped>
.modal-large {
  max-width: 900px;
}

.user-manage-container {
  display: flex;
  gap: 24px;
  min-height: 500px;
}

.user-list-panel {
  flex: 0 0 250px;
  border-right: 1px solid #f0f0f0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.user-item:hover {
  background: #f5f5f5;
}

.user-item.active {
  background: #e6f7ff;
  border-color: #1890ff;
}

.user-name {
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.user-role {
  font-size: 12px;
  color: #999;
}

.user-detail-panel {
  flex: 1;
  padding: 0 16px;
}

.user-detail-panel h4 {
  margin-bottom: 20px;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
  color: #666;
  font-size: 14px;
}

.form-item input,
.form-item select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  outline: none;
}

.form-item input:focus,
.form-item select:focus {
  border-color: #1890ff;
}
</style>
