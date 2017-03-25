import Vue from 'vue'
import Router from 'vue-router'
import Home from '@/components/Home'
import Session from '@/components/Session'

Vue.use(Router)

const homeRoute = {path: '/', name: 'Home', component: Home}
const sessionRoute = {path: '/session/:id', name: 'session',
	component: Session, props: true }
const routes = [homeRoute, sessionRoute]

export default new Router({
  routes: routes
})
