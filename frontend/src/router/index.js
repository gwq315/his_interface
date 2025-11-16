import { createRouter, createWebHistory } from 'vue-router'
import InterfaceList from '../views/InterfaceList.vue'
import InterfaceDetail from '../views/InterfaceDetail.vue'
import InterfaceForm from '../views/InterfaceForm.vue'
import DictionaryList from '../views/DictionaryList.vue'
import ProjectList from '../views/ProjectList.vue'
import DocumentList from '../views/DocumentList.vue'

const routes = [
  {
    path: '/',
    name: 'InterfaceList',
    component: InterfaceList
  },
  {
    path: '/interfaces',
    name: 'InterfaceListRoute',
    component: InterfaceList
  },
  {
    path: '/interfaces/:id',
    name: 'InterfaceDetail',
    component: InterfaceDetail,
    props: true
  },
  {
    path: '/interfaces/add',
    name: 'InterfaceAdd',
    component: InterfaceForm
  },
  {
    path: '/interfaces/edit/:id',
    name: 'InterfaceEdit',
    component: InterfaceForm,
    props: true
  },
  {
    path: '/dictionaries',
    name: 'DictionaryList',
    component: DictionaryList
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: ProjectList
  },
  {
    path: '/documents',
    name: 'DocumentList',
    component: DocumentList
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

