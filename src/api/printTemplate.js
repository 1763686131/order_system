/**
 * 打印模板 API
 */
import request from './request'

export function normalizePrintTemplate(template = {}) {
  return {
    ...template,
    businessType: template.businessType ?? template.business_type ?? '',
    paperType: template.paperType ?? template.paper_type ?? '',
    pageWidth: template.pageWidth ?? template.page_width ?? 210,
    pageHeight: template.pageHeight ?? template.page_height ?? 140,
    isDefault: Boolean(template.isDefault ?? template.is_default),
    enabled: Boolean(template.enabled ?? true),
    content: template.content ?? template.design ?? template.data ?? null,
    createdAt: template.createdAt ?? template.created_at ?? '',
    updatedAt: template.updatedAt ?? template.updated_at ?? ''
  }
}

/**
 * 获取所有模板
 * @param {Object} params - 查询参数
 * @param {string} params.businessType - 业务类型
 * @param {boolean} params.enabledOnly - 是否只返回启用模板
 */
export async function getTemplates(params = {}) {
  const response = await request({
    url: '/print-templates',
    method: 'GET',
    params
  })

  if (response?.success && Array.isArray(response.data)) {
    response.data = response.data.map(normalizePrintTemplate)
  }
  return response
}

/**
 * 获取单个模板
 * @param {number} id - 模板ID
 */
export async function getTemplate(id) {
  const response = await request({
    url: `/print-templates/${id}`,
    method: 'GET'
  })

  if (response?.success && response.data) {
    response.data = normalizePrintTemplate(response.data)
  }
  return response
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
export async function getDefaultTemplate(businessType) {
  const response = await getTemplates({
    businessType,
    enabledOnly: true
  })
  const templates = Array.isArray(response?.data) ? response.data : []
  return {
    ...response,
    data: templates.find(template => template.isDefault) || templates[0] || null
  }
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
