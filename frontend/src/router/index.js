import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../utils/auth'
import InterfaceList from '../views/InterfaceList.vue'
import InterfaceDetail from '../views/InterfaceDetail.vue'
import InterfaceForm from '../views/InterfaceForm.vue'
import DictionaryList from '../views/DictionaryList.vue'
import ProjectList from '../views/ProjectList.vue'
import DocumentList from '../views/DocumentList.vue'
import FAQList from '../views/FAQList.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'InterfaceList',
    component: InterfaceList,
    meta: { requiresAuth: true }
  },
  {
    path: '/interfaces',
    name: 'InterfaceListRoute',
    component: InterfaceList,
    meta: { requiresAuth: true }
  },
  {
    path: '/interfaces/:id',
    name: 'InterfaceDetail',
    component: InterfaceDetail,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/interfaces/add',
    name: 'InterfaceAdd',
    component: InterfaceForm,
    meta: { requiresAuth: true }
  },
  {
    path: '/interfaces/edit/:id',
    name: 'InterfaceEdit',
    component: InterfaceForm,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/dictionaries',
    name: 'DictionaryList',
    component: DictionaryList,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: ProjectList,
    meta: { requiresAuth: true }
  },
  {
    path: '/documents',
    name: 'DocumentList',
    component: DocumentList,
    meta: { requiresAuth: true }
  },
  {
    path: '/faqs',
    name: 'FAQList',
    component: FAQList,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  const isLoggedIn = isAuthenticated()
  
  if (requiresAuth && !isLoggedIn) {
    // 需要登录但未登录，跳转到登录页
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  } else if ((to.path === '/login' || to.path === '/register') && isLoggedIn) {
    // 已登录访问登录页或注册页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router

