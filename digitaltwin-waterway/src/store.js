import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    results: {}
  },
  actions: {
    async getResults () {
      const resp = await fetch('data/sample-result.json')
      const results = await resp.json()
      this.results = results
    }
  }
})
