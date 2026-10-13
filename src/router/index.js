import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import LoginView from '@/views/LoginView.vue'
import MainView from '@/views/MainView.vue'
import Admin from '@/views/Admin.vue'
import { getAdminRoutePermission, getDefaultAdminPath } from '@/utils/adminAccess'
import {
  ADMIN_DEPARTMENT_PERMISSIONS,
  ADMIN_EMPLOYEE_PERMISSIONS,
  ADMIN_OPERATION_LOG_PERMISSIONS,
  ADMIN_SALES_ORDER_PERMISSIONS,
  ADMIN_PURCHASE_ORDER_PERMISSIONS
} from '@/utils/accessControl'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/main',
    name: 'main',
    component: MainView,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'admin',
    component: Admin,
    meta: { requiresAuth: true, requiresAdmin: true },
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'finance/supplier-payments',
        name: 'admin-supplier-payments',
        component: () => import('@/views/admin/finance/PaymentHistory.vue'),
        props: { mode: 'payment' },
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/supplier-refunds',
        name: 'admin-supplier-refunds',
        redirect: to => ({ name: 'admin-supplier-payments', query: { ...to.query, tab: 'refund' } }),
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/supplier-reconciliations',
        name: 'admin-supplier-reconciliations',
        redirect: to => ({ name: 'admin-finance-payables', query: { ...to.query, tab: 'reconciliation' } }),
        meta: { requiresAuth: true }
      },
      {
        path: 'purchase/invoices',
        name: 'admin-purchase-invoices',
        redirect: to => ({
          name: 'admin-purchase-orders',
          query: to.query.documentId ? { invoiceId: to.query.documentId } : {}
        }),
        meta: { requiresAuth: true }
      },
      {
        path: 'purchase/returns',
        name: 'admin-purchase-returns',
        component: () => import('@/views/admin/purchase/PurchaseList.vue'),
        props: { mode: 'returns' },
        meta: { requiresAuth: true }
      },
      {
        path: 'purchase/returns/create',
        name: 'admin-purchase-return-create',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: { documentType: 'purchase-return', action: 'create' },
        meta: { requiresAuth: true, documentForm: true, permission: 'admin.purchase.return.create' }
      },
      {
        path: 'purchase/returns/edit/:id',
        name: 'admin-purchase-return-edit',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'purchase-return', action: 'edit', documentId: Number(route.params.id) }),
        meta: { requiresAuth: true, documentForm: true, permission: 'admin.purchase.return.edit' }
      },
      {
        path: 'purchase/returns/:id',
        name: 'admin-purchase-return-view',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'purchase-return', action: 'view', documentId: Number(route.params.id) }),
        meta: { requiresAuth: true, documentForm: true }
      },
      {
        path: 'finance/payables',
        name: 'admin-finance-payables',
        component: () => import('@/views/admin/finance/Receivables.vue'),
        props: { mode: 'payable' },
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/supplier-statement/:supplierId',
        name: 'admin-supplier-statement',
        redirect: to => ({
          name: 'admin-finance-debt-details',
          params: { type: 'payable', targetId: to.params.supplierId },
          query: to.query
        }),
        meta: { requiresAuth: true, permission: 'admin.finance.supplier_statement.read' }
      },
      {
        path: 'finance/employee-expenses',
        name: 'admin-employee-expenses',
        component: () => import('@/views/admin/finance/EmployeeExpenses.vue'),
        meta: { requiresAuth: true, permission: 'admin.finance.employee_expense.read' }
      },
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'products',
        name: 'admin-products',
        redirect: to => ({ name: 'admin-inventory', query: to.query, hash: to.hash }),
        meta: { requiresAuth: true }
      },
      {
        path: 'materials',
        name: 'admin-materials',
        redirect: to => ({ name: 'admin-inventory-materials', query: to.query, hash: to.hash }),
        meta: { requiresAuth: true }
      },
      {
        path: 'suppliers',
        name: 'admin-suppliers',
        redirect: '/admin/purchase/suppliers',
        meta: { requiresAuth: true }
      },
      {
        path: 'inventory',
        name: 'admin-inventory',
        component: () => import('@/views/admin/products/InventoryList.vue'),
        meta: { requiresAuth: true, productType: 'finished-product' }
      },
      {
        path: 'inventory/materials',
        name: 'admin-inventory-materials',
        component: () => import('@/views/admin/products/MaterialInventory.vue'),
        meta: { requiresAuth: true, productType: 'raw-material' }
      },
      {
        path: 'inventory/material-outbounds',
        name: 'admin-inventory-material-outbounds',
        component: () => import('@/views/admin/products/MaterialOutboundList.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'stock/in',
        name: 'admin-stock-in',
        component: () => import('@/views/admin/products/StockRecordList.vue'),
        props: { mode: 'INBOUND' },
        meta: { requiresAuth: true }
      },
      {
        path: 'stock/out',
        name: 'admin-stock-out',
        component: () => import('@/views/admin/products/StockRecordList.vue'),
        props: { mode: 'OUTBOUND' },
        meta: { requiresAuth: true }
      },
      {
        path: 'sales',
        name: 'admin-sales',
        component: () => import('@/views/admin/sales/UnifiedOrderList.vue'),
        props: { mode: 'finance' },
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/logistics',
        name: 'admin-sales-logistics',
        component: () => import('@/views/admin/sales/UnifiedOrderList.vue'),
        props: { mode: 'logistics' },
        meta: { requiresAuth: true }
      },
      {
        path: 'users',
        name: 'admin-users',
        redirect: '/admin/roles',
        meta: { requiresAuth: true }
      },
      {
        path: 'roles',
        name: 'admin-roles',
        component: () => import('@/views/admin/system/RoleGroupManage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'roles-legacy',
        name: 'admin-roles-legacy',
        redirect: '/admin/roles',
        meta: { requiresAuth: true }
      },
      {
        path: 'stores',
        name: 'admin-stores',
        component: () => import('@/views/admin/system/StoreManage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'settings',
        name: 'admin-settings',
        component: () => import('@/views/admin/system/Settings.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/receivables',
        name: 'admin-finance-receivables',
        component: () => import('@/views/admin/finance/Receivables.vue'),
        props: { mode: 'receivable' },
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/payment-history',
        name: 'admin-finance-payment-history',
        component: () => import('@/views/admin/finance/PaymentHistory.vue'),
        props: { mode: 'receipt' },
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/bank-accounts',
        name: 'admin-finance-bank-accounts',
        component: () => import('@/views/admin/finance/BankAccounts.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/logistics-truck',
        name: 'admin-finance-logistics-truck',
        component: () => import('@/views/admin/finance/LogisticsTruckReconciliation.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/express-courier',
        name: 'admin-finance-express-courier',
        component: () => import('@/views/admin/finance/ExpressCourierReconciliation.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/debt-details/:type/:targetId',
        name: 'admin-finance-debt-details',
        component: () => import('@/views/admin/finance/DebtDetails.vue'),
        props: to => ({
          type: to.params.type,
          targetId: to.params.targetId,
          targetName: typeof to.query.name === 'string' ? to.query.name : '',
          storeId: typeof to.query.storeId === 'string' ? to.query.storeId : ''
        }),
        meta: { requiresAuth: true, financeStatement: true }
      },
      {
        path: 'inventory/warehouse',
        name: 'admin-inventory-warehouse',
        component: () => import('@/views/admin/inventory/WarehouseManage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/customers',
        name: 'admin-customers',
        component: () => import('@/views/admin/sales/CustomerList.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/create',
        name: 'admin-sales-create',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'sale', action: route.query.copyFrom ? 'copy' : 'create' }),
        meta: {
          documentForm: true,
          requiresAuth: true,
          permission: ADMIN_SALES_ORDER_PERMISSIONS.CREATE
        }
      },
      {
        path: 'sales/edit/:id',
        name: 'admin-sales-edit',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'sale', action: 'edit', documentId: Number(route.params.id) }),
        meta: {
          documentForm: true,
          requiresAuth: true,
          permission: ADMIN_SALES_ORDER_PERMISSIONS.EDIT
        }
      },
      {
        path: 'purchase/orders',
        name: 'admin-purchase-orders',
        component: () => import('@/views/admin/purchase/PurchaseList.vue'),
        props: { mode: 'orders' },
        meta: { requiresAuth: true }
      },
      {
        path: 'purchase/orders/create',
        name: 'admin-purchase-order-create',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: { documentType: 'purchase-order', action: 'create' },
        meta: { requiresAuth: true, documentForm: true, permission: ADMIN_PURCHASE_ORDER_PERMISSIONS.CREATE }
      },
      {
        path: 'purchase/orders/edit/:id',
        name: 'admin-purchase-order-edit',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'purchase-order', action: 'edit', documentId: Number(route.params.id) }),
        meta: { requiresAuth: true, documentForm: true, permission: ADMIN_PURCHASE_ORDER_PERMISSIONS.EDIT }
      },
      {
        path: 'purchase/orders/audit/:id',
        name: 'admin-purchase-order-audit',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({
          documentType: 'purchase-order',
          action: 'audit',
          documentId: Number(route.params.id),
          sourceType: route.query.sourceType
        }),
        meta: { requiresAuth: true, documentForm: true, permission: ADMIN_PURCHASE_ORDER_PERMISSIONS.AUDIT }
      },
      {
        path: 'purchase/orders/:id',
        name: 'admin-purchase-order-view',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'purchase-order', action: 'view', documentId: Number(route.params.id) }),
        meta: { requiresAuth: true, documentForm: true }
      },
      {
        path: 'purchase/suppliers',
        name: 'admin-purchase-suppliers',
        component: () => import('@/views/admin/purchase/SupplierList.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'purchase/inbound',
        name: 'admin-purchase-inbound',
        component: () => import('@/views/admin/purchase/PurchaseList.vue'),
        props: { mode: 'inbound' },
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/returns',
        name: 'admin-sales-returns',
        component: () => import('@/views/admin/sales/ReturnOrderList.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'purchase/inbound/application/create',
        name: 'admin-purchase-inbound-application-create',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: { documentType: 'purchase-order', action: 'create', applicationMode: true },
        meta: { requiresAuth: true, documentForm: true, permission: 'admin.route.purchase.inbound' }
      },
      {
        path: 'purchase/inbound/application/edit/:id',
        name: 'admin-purchase-inbound-application-edit',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({
          documentType: 'purchase-order',
          action: 'edit',
          applicationMode: true,
          documentId: Number(route.params.id)
        }),
        meta: { requiresAuth: true, documentForm: true, permission: 'admin.route.purchase.inbound' }
      },
      {
        path: 'purchase/inbound/application/:id',
        name: 'admin-purchase-inbound-application-view',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({
          documentType: 'purchase-order',
          action: 'view',
          applicationMode: true,
          documentId: Number(route.params.id),
          printOnOpen: route.query.print === '1'
        }),
        meta: { requiresAuth: true, documentForm: true, permission: 'admin.route.purchase.inbound' }
      },
      {
        path: 'purchase/inbound/create',
        name: 'admin-purchase-inbound-create',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({
          documentType: 'purchase',
          action: 'create',
          purchaseOrderId: route.query.purchaseOrderId ? Number(route.query.purchaseOrderId) : null,
          supplement: route.query.supplement === '1',
          productType: route.query.productType || 'raw-material'
        }),
        meta: { requiresAuth: true, documentForm: true }
      },
      {
        path: 'purchase/inbound/edit/:id',
        name: 'admin-purchase-inbound-edit',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'purchase', action: 'edit', documentId: Number(route.params.id) }),
        meta: { requiresAuth: true, documentForm: true }
      },
      {
        path: 'purchase/inbound/:id',
        name: 'admin-purchase-inbound-view',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({ documentType: 'purchase', action: 'view', documentId: Number(route.params.id), printOnOpen: route.query.print === '1' }),
        meta: { requiresAuth: true, documentForm: true }
      },
      {
        path: 'sales/returns/create',
        name: 'admin-sales-return-create',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({
          documentType: 'sale-return', action: 'create',
          productType: route.query.productType || 'finished-product'
        }),
        meta: { requiresAuth: true, documentForm: true }
      },
      {
        path: 'sales/returns/edit/:id',
        name: 'admin-sales-return-edit',
        component: () => import('@/components/admin/BusinessDocumentForm.vue'),
        props: route => ({
          documentType: 'sale-return', action: 'edit', documentId: Number(route.params.id),
          productType: route.query.productType || 'finished-product'
        }),
        meta: { requiresAuth: true, documentForm: true }
      },
      {
        path: 'hr/reports',
        name: 'admin-hr-reports',
        component: () => import('@/views/admin/hr/Reports.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'hr/employees',
        name: 'admin-hr-employees',
        component: () => import('@/views/admin/hr/AccountManage.vue'),
        meta: {
          requiresAuth: true,
          permission: ADMIN_EMPLOYEE_PERMISSIONS.READ
        }
      },
      {
        path: 'hr/departments',
        name: 'admin-hr-departments',
        component: () => import('@/views/admin/hr/DepartmentManage.vue'),
        meta: {
          requiresAuth: true,
          permission: ADMIN_DEPARTMENT_PERMISSIONS.READ
        }
      },
      {
        path: 'system/print-template',
        name: 'admin-print-template',
        component: () => import('@/views/admin/system/PrintTemplate.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'system/operation-logs',
        name: 'admin-operation-logs',
        component: () => import('@/views/admin/system/OperationLogs.vue'),
        meta: {
          requiresAuth: true,
          permission: ADMIN_OPERATION_LOG_PERMISSIONS.READ
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()
  const loggedIn = await userStore.restoreSession()

  if (to.meta.requiresAuth && !loggedIn) {
    return {
      path: '/login',
      query: to.fullPath ? { redirect: to.fullPath } : {}
    }
  }

  if (to.meta.requiresAdmin && !userStore.canAccessAdmin) return '/main'

  if (['admin-finance-payables', 'admin-finance-receivables'].includes(to.name) && to.query.statementId) {
    const { statementId, tab, balanceSupplierId, ...query } = to.query
    if (typeof statementId !== 'string' || !/^[1-9]\d*$/.test(statementId)) return { path: to.path, query, replace: true }
    return {
      name: 'admin-finance-debt-details',
      params: { type: to.name === 'admin-finance-payables' ? 'payable' : 'receivable', targetId: statementId },
      query,
      replace: true
    }
  }
  if (to.name === 'admin-finance-debt-details') {
    const payable = to.params.type === 'payable'
    const listName = payable ? 'admin-finance-payables' : 'admin-finance-receivables'
    if (!['payable', 'receivable'].includes(to.params.type) || !/^[1-9]\d*$/.test(to.params.targetId)) {
      return { name: listName, replace: true }
    }
    if (payable && !userStore.hasPerm('admin.finance.supplier_statement.read')) return { name: listName, replace: true }
  }
  const adminPermission = getAdminRoutePermission(to.path)
  const canAccessNestedFinance = (
    to.path === '/admin/finance/supplier-payments' && to.query.tab === 'refund'
    && userStore.hasPerm('admin.route.finance.supplier_refunds')
  ) || (
    to.path === '/admin/finance/payables' && to.query.tab === 'reconciliation'
    && userStore.hasPerm('admin.route.finance.supplier_reconciliations')
  )
  const canAccessMergedInventory = (
    to.name === 'admin-inventory' && userStore.hasPerm('admin.route.products.list')
  ) || (
    to.name === 'admin-inventory-materials' && userStore.hasPerm('admin.route.products.materials')
  )
  if (
    adminPermission &&
    userStore.canAccessAdmin &&
    !userStore.hasPerm(adminPermission) && !canAccessNestedFinance && !canAccessMergedInventory
  ) {
    return getDefaultAdminPath(userStore)
  }

  if (to.meta.permission && !userStore.hasPerm(to.meta.permission)) {
    const fallbackPath = getDefaultAdminPath(userStore)
    return fallbackPath === to.path ? '/main' : fallbackPath
  }

  if (to.path === '/login' && loggedIn) {
    return userStore.canAccessAdmin ? getDefaultAdminPath(userStore) : '/main'
  }

  return true
})

export default router
