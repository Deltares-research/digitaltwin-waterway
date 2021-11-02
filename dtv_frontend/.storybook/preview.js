import Vue from 'vue';
import Vue2MapboxGL from 'vue2mapbox-gl'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
import 'mapbox-gl/dist/mapbox-gl.css'

Vue.use(Vue2MapboxGL)
Vue.use(Vuetify)

export const decorators = [(story) => ({
    components: { story },
    template: '<story />',
})];

export const parameters = {
  actions: { argTypesRegex: "^on[A-Z].*" },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
}
