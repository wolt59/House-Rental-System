import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/auth/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('../views/common/Home.vue') },
      { path: 'properties', name: 'PropertyList', component: () => import('../views/common/PropertyList.vue') },
      { path: 'properties/:id', name: 'PropertyDetail', component: () => import('../views/common/PropertyDetail.vue') },
      { path: 'news', name: 'NewsList', component: () => import('../views/common/NewsList.vue') },
      { path: 'news/:id', name: 'NewsDetail', component: () => import('../views/common/NewsDetail.vue') },
      { path: 'search', name: 'SmartSearch', component: () => import('../views/common/SmartSearch.vue') },
      { path: 'profile', name: 'Profile', component: () => import('../views/common/Profile.vue') },
      { path: 'messages', name: 'Messages', component: () => import('../views/common/Messages.vue') },
      {
        path: 'tenant',
        meta: { role: 'tenant' },
        children: [
          { path: 'bookings', name: 'TenantBookings', component: () => import('../views/tenant/Bookings.vue') },
          { path: 'contracts', name: 'TenantContracts', component: () => import('../views/tenant/Contracts.vue') },
          { path: 'payments', name: 'TenantPayments', component: () => import('../views/tenant/Payments.vue') },
          { path: 'maintenance', name: 'TenantMaintenance', component: () => import('../views/tenant/Maintenance.vue') },
          { path: 'complaints', name: 'TenantComplaints', component: () => import('../views/tenant/Complaints.vue') },
        ],
      },
      {
        path: 'landlord',
        meta: { role: 'landlord' },
        children: [
          { path: 'properties', name: 'LandlordProperties', component: () => import('../views/landlord/Properties.vue') },
          { path: 'bookings', name: 'LandlordBookings', component: () => import('../views/landlord/Bookings.vue') },
          { path: 'contracts', name: 'LandlordContracts', component: () => import('../views/landlord/Contracts.vue') },
          { path: 'payments', name: 'LandlordPayments', component: () => import('../views/landlord/Payments.vue') },
          { path: 'news', name: 'LandlordNews', component: () => import('../views/landlord/News.vue') },
        ],
      },
      {
        path: 'admin',
        meta: { role: 'admin' },
        children: [
          { path: 'dashboard', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue') },
          { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue') },
          { path: 'properties', name: 'AdminProperties', component: () => import('../views/admin/Properties.vue') },
          { path: 'audit-logs', name: 'AdminAuditLogs', component: () => import('../views/admin/AuditLogs.vue') },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.meta.guest && token) {
    return next('/')
  }
  if (!to.meta.guest && !token && to.path !== '/login') {
    const publicPaths = ['/', '/properties', '/news', '/search']
    if (publicPaths.some((p) => to.path.startsWith(p))) {
      return next()
    }
    return next('/login')
  }
  if (to.meta.role && user && user.role !== to.meta.role && user.role !== 'admin') {
    return next('/')
  }
  next()
})

export default router
