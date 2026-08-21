import request from './request'

// 获取原材料数据
export function getMaterials() {
  return request({
    url: '/materials',
    method: 'GET'
  })
}

// 创建原材料记录
export function createMaterial(materialData) {
  return request({
    url: '/materials',
    method: 'POST',
    data: materialData
  })
}

// 更新原材料记录
export function updateMaterial(materialId, materialData) {
  return request({
    url: `/materials/${materialId}`,
    method: 'PUT',
    data: materialData
  })
}

// 删除原材料记录
export function deleteMaterial(materialId) {
  return request({
    url: `/materials/${materialId}`,
    method: 'DELETE'
  })
}
