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

      const apiUrl = process.env.VUE_APP_API_URI
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
    async findRoute({ commit }, payload) {
      const apiUrl = process.env.VUE_APP_API_URI

      // only store the waypoints
      const waypoints = payload.map(feature => feature.properties.n)

      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ waypoints: waypoints })
      }
      const resp = await fetch(`${apiUrl}/find_route`, requestOptions)
      const body = await resp.json()
      console.log('route', body)
      commit('setRoute', body)
    },
    async addWaypoint({ dispatch, commit, state }, payload) {
      commit('addWaypoint', payload)
      if (state.waypoints.length > 1) {
        dispatch('findRoute', state.waypoints)
      }
    },
    async removeWaypoint({ dispatch, commit, state }, payload) {
      commit('removeWaypoint', payload)
      dispatch('findRoute', state.waypoints)
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
      const defaultProperties = {
        'Dry Bulk': {
          name: feature.properties.n,
          cargoType: 'Dry Bulk',
          level: 10000,
          loadingRate: 200,
          loadingRateVariation: 100
        },
        Container: {
          name: feature.properties.n,
          cargoType: 'Container',
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

      this.dispatch('findRoute', state.waypoints)
    }
  }
})
