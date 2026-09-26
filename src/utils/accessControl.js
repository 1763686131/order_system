const SCOPE_FIELDS = {
  store: {
    allKey: 'allStores',
    idsKey: 'storeIds'
  },
  warehouse: {
    allKey: 'allWarehouses',
    idsKey: 'warehouseIds'
  }
}

export const ADMIN_SALES_ORDER_PERMISSIONS = {
  CREATE: 'admin.sales.order.create',
  EDIT: 'admin.sales.order.edit',
  DELETE: 'admin.sales.order.delete',
  PRINT: 'admin.sales.order.print',
  EXPORT: 'admin.sales.order.export',
  COMPLETE: 'admin.sales.order.complete',
  REOPEN: 'admin.sales.order.reopen',
  AUDIT: 'admin.sales.order.audit',
  REVERSE_AUDIT: 'admin.sales.order.reverse_audit'
}

export const ADMIN_EMPLOYEE_PERMISSIONS = {
  READ: 'admin.employee.read',
  DETAIL: 'admin.employee.detail',
  CREATE: 'admin.employee.create',
  EDIT: 'admin.employee.edit',
  DELETE: 'admin.employee.delete'
}

export const ADMIN_DEPARTMENT_PERMISSIONS = {
  READ: 'admin.department.read',
  CREATE: 'admin.department.create',
  EDIT: 'admin.department.edit',
  DELETE: 'admin.department.delete'
}

export const ADMIN_OPERATION_LOG_PERMISSIONS = {
  READ: 'admin.operation_log.read',
  CLEAR: 'admin.operation_log.clear'
}

export const ADMIN_LOGISTICS_COPY_PERMISSIONS = {
  ENTRY: 'admin.logistics_copy.entry',
  READ: 'admin.logistics_copy.read',
  CREATE: 'admin.logistics_copy.create',
  EDIT: 'admin.logistics_copy.edit',
  DELETE: 'admin.logistics_copy.delete'
}

const normalizeIds = (values) => {
  if (!Array.isArray(values)) return []
  return [...new Set(values.map(Number).filter(Number.isInteger))]
}

export function normalizeAccessState(userData = {}) {
  return {
    isSuperAdmin: Boolean(userData.isSuperAdmin),
    canAccessAdmin: Boolean(userData.canAccessAdmin),
    longSession: Boolean(userData.longSession),
    allStores: Boolean(userData.allStores || userData.isSuperAdmin),
    allWarehouses: Boolean(userData.allWarehouses || userData.isSuperAdmin),
    storeIds: normalizeIds(userData.storeIds),
    warehouseIds: normalizeIds(userData.warehouseIds),
    permissions: Array.isArray(userData.permissions) ? userData.permissions : []
  }
}

export function mergeRoleScopes(roles = [], availableScopes = {}) {
  const fullAccess = roles.some(role => role.fullAccess)
  return {
    allStores: fullAccess,
    allWarehouses: fullAccess,
    storeIds: fullAccess
      ? normalizeIds(availableScopes.storeIds)
      : normalizeIds(roles.flatMap(role => role.storeIds || [])),
    warehouseIds: fullAccess
      ? normalizeIds(availableScopes.warehouseIds)
      : normalizeIds(roles.flatMap(role => role.warehouseIds || []))
  }
}

export function mergeRolePermissions(roles = []) {
  return [...new Set(roles.flatMap(role => role.permissionCodes || []))]
}

export function hasPermission(user, permissionCode) {
  return Boolean(
    user?.isSuperAdmin ||
    (permissionCode && user?.permissions?.includes(permissionCode))
  )
}

export function getAccessibleScopeIds(user, scopeType) {
  const config = SCOPE_FIELDS[scopeType]
  if (!config) return new Set()
  if (user?.isSuperAdmin || user?.[config.allKey]) return null
  return new Set(normalizeIds(user?.[config.idsKey]))
}

export function canAccessScope(user, scopeType, scopeId) {
  const accessibleIds = getAccessibleScopeIds(user, scopeType)
  if (accessibleIds === null) return true
  const normalizedId = Number(scopeId)
  return Number.isInteger(normalizedId) &&
    accessibleIds.has(normalizedId)
}

export function filterAccessibleOptions(options, user, scopeType) {
  const accessibleIds = getAccessibleScopeIds(user, scopeType)
  if (accessibleIds === null) return options
  return options.filter(option => accessibleIds.has(Number(option.id)))
}

export function filterRecordsByScope(records, user, scopeType, scopeIdGetter) {
  const accessibleIds = getAccessibleScopeIds(user, scopeType)
  if (accessibleIds === null) return records
  return records.filter(record => accessibleIds.has(Number(scopeIdGetter(record))))
}

export function hasMultipleScopeOptions(options) {
  return options.length > 1
}
