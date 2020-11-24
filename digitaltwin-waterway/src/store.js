import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    results: {},
    sites: []
  },
  actions: {
    async fetchResults () {
      const resp = await fetch('data/sample-result.json')
      const results = await resp.json()
      this.commit('results', results)
    },
    async fetchSites () {
      const resp = await fetch('data/sites.json')
      const sites = await resp.json()
      this.commit('setSites', sites)
    }
  },
  mutations: {
    setResults (state, results) {
      state.results = results
    },
    setSites (state, sites) {
      state.sites = sites
    }

  }
})
