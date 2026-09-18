import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import LoginView from '@/views/LoginView.vue'
import MainView from '@/views/MainView.vue'
import Admin from '@/views/Admin.vue'

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
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'products',
        name: 'admin-products',
        component: () => import('@/views/admin/products/ProductList.vue'),
        meta: { requiresAuth: true, productType: 'finished-product' }
      },
      {
        path: 'materials',
        name: 'admin-materials',
        component: () => import('@/views/admin/products/MaterialProductList.vue'),
        meta: { requiresAuth: true, productType: 'raw-material' }
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
        meta: { requiresAuth: true }
      },
      {
        path: 'inventory/materials',
        name: 'admin-inventory-materials',
        component: () => import('@/views/admin/products/MaterialInventory.vue'),
        meta: { requiresAuth: true }
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
        component: () => import('@/views/admin/system/RoleManage.vue'),
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
        meta: { requiresAuth: true }
      },
      {
        path: 'finance/payment-history',
        name: 'admin-finance-payment-history',
        component: () => import('@/views/admin/finance/PaymentHistory.vue'),
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
        meta: { requiresAuth: true },
        props: (route) => ({
          type: route.params.type,
          targetId: route.params.targetId,
          targetName: route.query.name || ''
        })
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
        component: () => import('@/views/admin/sales/OrderForm.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/edit/:id',
        name: 'admin-sales-edit',
        component: () => import('@/views/admin/sales/OrderForm.vue'),
        props: route => ({ orderId: Number(route.params.id) }),
        meta: { requiresAuth: true }
      },
      {
        path: 'purchase/orders',
        name: 'admin-purchase-orders',
        component: () => import('@/views/admin/purchase/PurchaseOrders.vue'),
        meta: { requiresAuth: true }
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
        component: () => import('@/views/admin/purchase/PurchaseInbound.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/returns',
        name: 'admin-sales-returns',
        component: () => import('@/views/admin/sales/ReturnOrderList.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/returns/create',
        name: 'admin-sales-return-create',
        component: () => import('@/views/admin/sales/ReturnOrderForm.vue'),
        props: route => ({
          productType: route.query.productType || 'finished-product'
        }),
        meta: { requiresAuth: true }
      },
      {
        path: 'sales/returns/edit/:id',
        name: 'admin-sales-return-edit',
        component: () => import('@/views/admin/sales/ReturnOrderForm.vue'),
        props: route => ({
          returnId: Number(route.params.id),
          productType: route.query.productType || 'finished-product'
        }),
        meta: { requiresAuth: true }
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
        meta: { requiresAuth: true }
      },
      {
        path: 'system/print-template',
        name: 'admin-print-template',
        component: () => import('@/views/admin/system/PrintTemplate.vue'),
        meta: { requiresAuth: true }
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

  if (to.path === '/login' && loggedIn) {
    return userStore.canAccessAdmin ? '/admin/dashboard' : '/main'
  }

  return true
})

export default router
