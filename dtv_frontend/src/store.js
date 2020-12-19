import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    results: {},
    sites: [],
    shipState: 0,
    play: false
  },
  actions: {
    async fetchResults ({ commit }, config) {
      console.log('config', config)
      const request = {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config) // body data type must match "Content-Type" header
      }
      console.log('env', process.env)
      const apiUrl = process.env.VUE_APP_API_URL
      const resp = await fetch(`${apiUrl}/simulate`, request)
      const results = await resp.json()
      commit('setResults', results)
    },
    async fetchSites ({ commit }) {
      const resp = await fetch('data/sites.json')
      const sites = await resp.json()
      console.log('sites', sites)
      sites.features = sites.features.map(
        feature => {
          return feature
        }
      )
      commit('setSites', sites)
    }
  },
  mutations: {
    setResults (state, results) {
      state.results = results
    },
    setSites (state, sites) {
      state.sites = sites
    },
    setPlay (state, play) {
      state.play = play
    },
    setShipState (state, shipState) {
      state.shipState = shipState
    }
  }
})
