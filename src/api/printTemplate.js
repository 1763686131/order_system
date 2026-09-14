/**
 * 打印模板 API
 */
import request from './request'

/**
 * 获取所有模板
 * @param {Object} params - 查询参数
 * @param {string} params.businessType - 业务类型
 * @param {boolean} params.enabled - 是否启用
 */
export function getTemplates(params = {}) {
  return request({
    url: '/print-templates',
    method: 'GET',
    params
  })
}

/**
 * 获取单个模板
 * @param {number} id - 模板ID
 */
export function getTemplate(id) {
  return request({
    url: `/print-templates/${id}`,
    method: 'GET'
  })
}

/**
 * 创建模板
 * @param {Object} data - 模板数据
 */
export function createTemplate(data) {
  return request({
    url: '/print-templates',
    method: 'POST',
    data
  })
}

/**
 * 更新模板
 * @param {number} id - 模板ID
 * @param {Object} data - 模板数据
 */
export function updateTemplate(id, data) {
  return request({
    url: `/print-templates/${id}`,
    method: 'PUT',
    data
  })
}

/**
 * 删除模板
 * @param {number} id - 模板ID
 */
export function deleteTemplate(id) {
  return request({
    url: `/print-templates/${id}`,
    method: 'DELETE'
  })
}

/**
 * 设置默认模板
 * @param {number} id - 模板ID
 */
export function setDefaultTemplate(id) {
  return request({
    url: `/print-templates/${id}/set-default`,
    method: 'POST'
  })
}

/**
 * 获取默认模板
 * @param {string} businessType - 业务类型
 */
export function getDefaultTemplate(businessType) {
  return request({
    url: `/print-templates/default/${businessType}`,
    method: 'GET'
  })
}

/**
 * 从 localStorage 迁移数据到数据库
 * @param {Array} templates - 模板数据数组
 */
export function migrateTemplates(templates) {
  return request({
    url: '/print-templates/migrate',
    method: 'POST',
    data: { templates }
  })
}
