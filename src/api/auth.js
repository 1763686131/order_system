import request from './request'

// 登录
export function login(username, password) {
  return request({
    url: '/login',
    method: 'POST',
    data: { username, password }
  })
}

// 登出
export function logout() {
  return request({
    url: '/logout',
    method: 'POST'
  })
}
