import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from './views/Home'
import Ships from './views/Ships'

Vue.use(VueRouter)

const routes = [
  { path: '/', component: Home },
  { path: '/ships', component: Ships }
]

const router = new VueRouter({
  routes // short for `routes: routes`
})

export default router
