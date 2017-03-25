// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import Vuetify from 'vuetify'
import App from './App'
import router from './router'
import store from './store'
import './utils/utilities'
import Chart from 'chart.js'

window.Chart = Chart

// Disable annoying "tips".
Vue.config.productionTip = false

// Use Vuetify for making nice looking components, etc.
Vue.use(Vuetify)

/* eslint-disable no-new */
var app = new Vue({
  el: '#app',
  store,
  router,
  template: '<App/>',
  components: { App }
})

// For programmatic navigation in the store.
window.router = app.$router
