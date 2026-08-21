import request from './request'

// 获取用户列表
export function getUsers() {
  return request({
    url: '/users',
    method: 'GET'
  })
}

// 创建用户
export function createUser(userData) {
  return request({
    url: '/users',
    method: 'POST',
    data: userData
  })
}

// 更新用户
export function updateUser(userId, userData) {
  return request({
    url: `/users/${userId}`,
    method: 'PUT',
    data: userData
  })
}

// 删除用户
export function deleteUser(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'DELETE'
  })
}

// 更新用户密码
export function updateUserPassword(userId, newPassword) {
  return request({
    url: `/users/${userId}/password`,
    method: 'PUT',
    data: { password: newPassword }
  })
}
