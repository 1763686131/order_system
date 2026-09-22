import { ADMIN_EMPLOYEE_PERMISSIONS } from '@/utils/accessControl'

export const ADMIN_ROUTE_PERMISSIONS = {
  DASHBOARD: 'admin.route.dashboard',
  PRODUCTS: 'admin.route.products',
  SALES: 'admin.route.sales',
  PURCHASE: 'admin.route.purchase',
  INVENTORY: 'admin.route.inventory',
  FINANCE: 'admin.route.finance',
  HR: 'admin.route.hr',
  SYSTEM: 'admin.route.system'
}

export const ADMIN_ROUTE_ENTRIES = [
  { permission: ADMIN_ROUTE_PERMISSIONS.DASHBOARD, path: '/admin/dashboard' },
  { permission: ADMIN_ROUTE_PERMISSIONS.PRODUCTS, path: '/admin/products' },
  { permission: ADMIN_ROUTE_PERMISSIONS.SALES, path: '/admin/sales' },
  { permission: ADMIN_ROUTE_PERMISSIONS.PURCHASE, path: '/admin/purchase/orders' },
  { permission: ADMIN_ROUTE_PERMISSIONS.INVENTORY, path: '/admin/inventory' },
  { permission: ADMIN_ROUTE_PERMISSIONS.FINANCE, path: '/admin/finance/receivables' },
  { permission: ADMIN_EMPLOYEE_PERMISSIONS.READ, path: '/admin/hr/employees' },
  { permission: ADMIN_ROUTE_PERMISSIONS.HR, path: '/admin/hr/reports' },
  { permission: ADMIN_ROUTE_PERMISSIONS.SYSTEM, path: '/admin/settings' }
]

export function getDefaultAdminPath(userStore) {
  const entry = ADMIN_ROUTE_ENTRIES.find(item => userStore.hasPerm(item.permission))
  return entry?.path || '/main'
}

export function getAdminRoutePermission(path = '') {
  if (path === '/admin/dashboard') return ADMIN_ROUTE_PERMISSIONS.DASHBOARD
  if (/^\/admin\/(products|materials)(\/|$)/.test(path)) {
    return ADMIN_ROUTE_PERMISSIONS.PRODUCTS
  }
  if (/^\/admin\/sales(\/|$)/.test(path)) return ADMIN_ROUTE_PERMISSIONS.SALES
  if (/^\/admin\/(purchase|suppliers)(\/|$)/.test(path)) {
    return ADMIN_ROUTE_PERMISSIONS.PURCHASE
  }
  if (/^\/admin\/(inventory|stock)(\/|$)/.test(path)) {
    return ADMIN_ROUTE_PERMISSIONS.INVENTORY
  }
  if (/^\/admin\/finance(\/|$)/.test(path)) return ADMIN_ROUTE_PERMISSIONS.FINANCE
  if (path === '/admin/hr/employees') return null
  if (/^\/admin\/hr(\/|$)/.test(path)) return ADMIN_ROUTE_PERMISSIONS.HR
  if (/^\/admin\/(stores|settings|roles|users|system)(\/|$)/.test(path)) {
    return ADMIN_ROUTE_PERMISSIONS.SYSTEM
  }
  return null
}
