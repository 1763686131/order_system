import {
  ADMIN_DEPARTMENT_PERMISSIONS,
  ADMIN_EMPLOYEE_PERMISSIONS
} from '@/utils/accessControl'

export const ADMIN_ROUTE_PERMISSIONS = {
  DASHBOARD: 'admin.route.dashboard'
}

export const ADMIN_ROUTE_BRANCH_PERMISSIONS = {
  PRODUCTS: {
    LIST: 'admin.route.products.list',
    MATERIALS: 'admin.route.products.materials'
  },
  SALES: {
    ORDERS: 'admin.route.sales.orders',
    LOGISTICS: 'admin.route.sales.logistics',
    RETURNS: 'admin.route.sales.returns',
    CUSTOMERS: 'admin.route.sales.customers'
  },
  PURCHASE: {
    ORDERS: 'admin.route.purchase.orders',
    SUPPLIERS: 'admin.route.purchase.suppliers',
    INBOUND: 'admin.route.purchase.inbound'
  },
  INVENTORY: {
    PRODUCTS: 'admin.route.inventory.products',
    MATERIALS: 'admin.route.inventory.materials',
    MATERIAL_OUTBOUNDS: 'admin.route.inventory.material_outbounds',
    STOCK_IN: 'admin.route.inventory.stock_in',
    STOCK_OUT: 'admin.route.inventory.stock_out',
    WAREHOUSE: 'admin.route.inventory.warehouse'
  },
  FINANCE: {
    RECEIVABLES: 'admin.route.finance.receivables',
    PAYMENT_HISTORY: 'admin.route.finance.payment_history',
    BANK_ACCOUNTS: 'admin.route.finance.bank_accounts',
    LOGISTICS_TRUCK: 'admin.route.finance.logistics_truck',
    EXPRESS_COURIER: 'admin.route.finance.express_courier'
  },
  HR: {
    EMPLOYEES: ADMIN_EMPLOYEE_PERMISSIONS.READ,
    DEPARTMENTS: ADMIN_DEPARTMENT_PERMISSIONS.READ,
    COMPANY: 'admin.route.hr.company',
    REPORTS: 'admin.route.hr.reports'
  },
  SYSTEM: {
    STORES: 'admin.route.system.stores',
    SETTINGS: 'admin.route.system.settings',
    ROLES: 'admin.route.system.roles',
    PRINT_TEMPLATE: 'admin.route.system.print_template'
  }
}

export const ADMIN_ROUTE_ENTRIES = [
  { permission: ADMIN_ROUTE_PERMISSIONS.DASHBOARD, path: '/admin/dashboard' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.LIST, path: '/admin/products' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.MATERIALS, path: '/admin/materials' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS, path: '/admin/sales' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.LOGISTICS, path: '/admin/sales/logistics' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.RETURNS, path: '/admin/sales/returns' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.CUSTOMERS, path: '/admin/sales/customers' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.ORDERS, path: '/admin/purchase/orders' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.SUPPLIERS, path: '/admin/purchase/suppliers' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.INBOUND, path: '/admin/purchase/inbound' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.PRODUCTS, path: '/admin/inventory' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIALS, path: '/admin/inventory/materials' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIAL_OUTBOUNDS, path: '/admin/inventory/material-outbounds' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.STOCK_IN, path: '/admin/stock/in' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.STOCK_OUT, path: '/admin/stock/out' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.WAREHOUSE, path: '/admin/inventory/warehouse' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.RECEIVABLES, path: '/admin/finance/receivables' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.PAYMENT_HISTORY, path: '/admin/finance/payment-history' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.BANK_ACCOUNTS, path: '/admin/finance/bank-accounts' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.LOGISTICS_TRUCK, path: '/admin/finance/logistics-truck' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.EXPRESS_COURIER, path: '/admin/finance/express-courier' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.EMPLOYEES, path: '/admin/hr/employees' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.DEPARTMENTS, path: '/admin/hr/departments' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.COMPANY, path: '/admin/hr/company' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.REPORTS, path: '/admin/hr/reports' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.STORES, path: '/admin/stores' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.SETTINGS, path: '/admin/settings' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.ROLES, path: '/admin/roles' },
  { permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.PRINT_TEMPLATE, path: '/admin/system/print-template' }
]

export function getDefaultAdminPath(userStore) {
  const entry = ADMIN_ROUTE_ENTRIES.find(item => userStore.hasPerm(item.permission))
  return entry?.path || '/main'
}

export function getAdminRoutePermission(path = '') {
  if (path === '/admin/dashboard') return ADMIN_ROUTE_PERMISSIONS.DASHBOARD
  if (path === '/admin/products') return ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.LIST
  if (path === '/admin/materials') return ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.MATERIALS
  if (/^\/admin\/sales\/returns(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.RETURNS
  }
  if (/^\/admin\/sales\/logistics(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.LOGISTICS
  }
  if (/^\/admin\/sales\/customers(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.CUSTOMERS
  }
  if (/^\/admin\/sales(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS
  }
  if (/^\/admin\/(purchase\/suppliers|suppliers)(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.SUPPLIERS
  }
  if (/^\/admin\/purchase\/inbound(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.INBOUND
  }
  if (/^\/admin\/purchase(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.ORDERS
  }
  if (/^\/admin\/inventory\/materials(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIALS
  }
  if (/^\/admin\/inventory\/material-outbounds(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIAL_OUTBOUNDS
  }
  if (/^\/admin\/inventory\/warehouse(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.WAREHOUSE
  }
  if (/^\/admin\/stock\/in(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.STOCK_IN
  }
  if (/^\/admin\/stock\/out(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.STOCK_OUT
  }
  if (/^\/admin\/inventory(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.PRODUCTS
  }
  if (/^\/admin\/finance\/debt-details(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.RECEIVABLES
  }
  if (/^\/admin\/finance\/payment-history(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.PAYMENT_HISTORY
  }
  if (/^\/admin\/finance\/bank-accounts(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.BANK_ACCOUNTS
  }
  if (/^\/admin\/finance\/logistics-truck(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.LOGISTICS_TRUCK
  }
  if (/^\/admin\/finance\/express-courier(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.EXPRESS_COURIER
  }
  if (/^\/admin\/finance\/receivables(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.RECEIVABLES
  }
  if (path === '/admin/hr/employees') return ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.EMPLOYEES
  if (path === '/admin/hr/departments') return ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.DEPARTMENTS
  if (/^\/admin\/hr\/company(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.COMPANY
  }
  if (/^\/admin\/hr\/reports(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.REPORTS
  }
  if (/^\/admin\/stores(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.STORES
  }
  if (/^\/admin\/settings(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.SETTINGS
  }
  if (/^\/admin\/(roles|roles-legacy|users)(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.ROLES
  }
  if (/^\/admin\/system\/print-template(\/|$)/.test(path)) {
    return ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.PRINT_TEMPLATE
  }
  return null
}
