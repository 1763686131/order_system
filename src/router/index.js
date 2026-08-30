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
    meta: { requiresAuth: true },
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
        meta: { requiresAuth: true }
      },
      {
        path: 'orders',
        name: 'admin-orders',
        component: () => import('@/views/admin/orders/UnifiedOrderList.vue'),
        props: { mode: 'finance' },
        meta: { requiresAuth: true }
      },
      {
        path: 'orders/logistics',
        name: 'admin-orders-logistics',
        component: () => import('@/views/admin/orders/UnifiedOrderList.vue'),
        props: { mode: 'logistics' },
        meta: { requiresAuth: true }
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('@/views/admin/system/UserManage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'roles',
        name: 'admin-roles',
        component: () => import('@/views/admin/system/RoleManage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'stores',
        name: 'admin-stores',
        component: () => import('@/views/admin/system/StoreManage.vue'),
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
        path: 'inventory/warehouse',
        name: 'admin-inventory-warehouse',
        component: () => import('@/views/admin/inventory/WarehouseManage.vue'),
        meta: { requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/main')
  } else {
    next()
  }
})

export default router
