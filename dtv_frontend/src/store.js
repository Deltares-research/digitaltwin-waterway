import Vue from 'vue'
import Vuex from 'vuex'
import { getField, updateField } from 'vuex-map-fields'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    // general cargo type
    // used to define units and other defaults
    cargoType: '',

    results: {},
    // sites extra information on known locations
    // current selected node (which can be added to the route)
    selectedWaypoint: null,
    // the computed route
    route: [],
    // the waypoints that the route should go through
    // list of features
    waypoints: [],

    // animation type
    currentTime: null,
    progress: 0,
    play: false
  },
  getters: {
    getField,
    unit(state) {
      let unit = ''
      const cargoType = state.cargoType
      if (cargoType === 'Dry Bulk') {
        unit = 'Tonne'
      } else if (cargoType === 'Container') {
        unit = 'TEU'
      }
      return unit
    }
  },
  actions: {
    async fetchResults({ commit }, config) {
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
    async fetchSites({ commit }) {
      const resp = await fetch('data/sites.json')
      const sites = await resp.json()
      console.log('sites', sites)
      sites.features = sites.features.map(feature => {
        return feature
      })
      commit('setSites', sites)
    },
    async fetchRoute({ commit }) {
      const resp = await fetch('data/routes.json')
      const body = await resp.json()
      console.log('route', body)
      commit('setRoute', body.route)
    },
    async fetchRoutev2({ commit }) {
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ waypoints: ['A', 'B'] })
      }
      const resp = await fetch('get_routes', requestOptions)
      const body = await resp.json()
      console.log('route', body)
      commit('setRoute', body.route)
    }
  },
  mutations: {
    updateField,
    setRoute(state, payload) {
      state.route = payload
    },
    setSites(state, payload) {
      state.sites = payload
    },
    setResults(state, payload) {
      state.results = payload
    },
    addWaypoint(state, payload) {
      const feature = payload
      if (!feature.properties.n) {
        return
      }
      if (!feature.properties.name) {
        feature.properties.name = feature.properties.n
      }

      const defaultProperties = {
        'Dry Bulk': {
          level: 10000,
          loadingRate: 200,
          loadingRateVariation: 100
        },
        Container: {
          level: 1000,
          loadingRate: 20,
          loadingRateVariation: 10
        }
      }

      feature.properties = {
        ...feature.properties,
        ...defaultProperties[state.cargoType]
      }
      console.log('adding waypoint', feature)

      // check if waypoint is already add the end or remove doubles
      state.waypoints.push(feature)
    },
    removeWaypoint(state, payload) {
      // do nothing if not the correct item
      const { index } = payload
      state.waypoints.splice(index, 1)
    }
  }
})
