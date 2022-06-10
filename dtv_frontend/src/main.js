import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import './plugins/vue2mapbox-gl'
import './plugins/vue-echarts'
import store from './store'
import router from './router'
import mitt from 'mitt'

Vue.config.productionTip = false

const bus = mitt()

new Vue({
  vuetify,
  store,
  router,
  render: h => h(App),
  provide: {
    bus
  }
}).$mount('#app')
