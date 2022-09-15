import Vue from 'vue'
import Vuex from 'vuex'

import _ from 'lodash'

import { getField, updateField } from 'vuex-map-fields'

import buffer from '@turf/buffer'
// hardcode the prototype ships so we can build our per shipstype properties
import prototypeShips from '../public/data/DTV_shiptypes_database.json'

// cleanup prototype ships
_.forEach(prototypeShips, ship => {
  ship.capacity = ship['Load Weight average [ton]']
  ship.name = ship['Description (English)']
  ship.count = 0
})

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

    // selected ships
    fleet: [],
    // prototype ships
    prototypeShips: prototypeShips,

    // feature collection with water levels
    waterlevels: { type: 'FeatureCollection', features: [] },
    waterlevelBuffers: { type: 'FeatureCollection', features: [] },
    bathymetry: { type: 'FeatureCollection', features: [] },
    bathymetryBuffers: { type: 'FeatureCollection', features: [] },
    velocities: { type: 'FeatureCollection', features: [] },
    // animation type
    currentTime: null,
    progress: 0,
    play: false,
    climate: {},
    chartTripDuration: {},
    chartDurationBreakdown: {},
    chartTrips: {}
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
    },
    expandedFleet(state) {
      // converts them to feature collection called a fleet
      // fleet is not available yet
      const route = state.route
      // convert fleet to geojson object
      const fleet = []
      // repeat for count of each ship
      state.fleet.forEach((ship, i) => {
        let geometry = null
        if (route.features?.length) {
          geometry = route.features[0].geometry
        }
        const feature = {
          type: 'Feature',
          id: i,
          geometry: geometry,
          properties: ship
        }
        for (i; i < ship.count; i++) {
          fleet.push(feature)
        }
      })
      return fleet
    },
    config(state, getters) {
      let sites = []
      if (state.waypoints?.length >= 1) {
        sites = [_.first(state.waypoints), _.last(state.waypoints)]
      }
      const config = {
        route: state.route.features,
        waypoints: state.waypoints,
        sites: sites,
        fleet: getters.expandedFleet,
        operator: { name: 'Operator' },
        climate: state.climate,
        // get the list of quantities
        quantities: {
          bathymetry: state.bathymetry,
          waterlevels: state.waterlevels,
          velocities: state.velocities
        },
        options: {
          has_berth: true
        }
      }
      console.log('config', config)
      return config
    }
  },
  actions: {
    async fetchResults({ commit, dispatch }, config) {
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
      const resp = await fetch(`${apiUrl}/v3/simulate`, request)
      const results = await resp.json()
      commit('setResults', results)
      dispatch('fetchKPIs', results)
    },
    async fetchKPIs({ commit }, results) {
      console.log('fetching KPI for ', results)
      const request = {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(results)
      }
      const apiUrl = process.env.VUE_APP_API_URI
      const resp = await fetch(`${apiUrl}/charts/trip_duration`, request)
      const tripDuration = await resp.json()
      commit('setChartTripDuration', tripDuration)
      const resp = await fetch(`${apiUrl}/charts/duration_breakdown`, request)
      const durationBreakdown = await resp.json()
      commit('setChartDurationBreakdown', durationBreakdown)
      const resp = await fetch(`${apiUrl}/charts/trips`, request)
      const trips = await resp.json()
      commit('setChartTrips', trips)
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
    async computeWaterlevels({ commit }, payload) {
      const apiUrl = process.env.VUE_APP_API_URI

      // only store the waypoints
      const climate = payload

      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ climate })
      }
      const resp = await fetch(`${apiUrl}/waterlevels`, requestOptions)
      const body = await resp.json()
      console.log('waterlevels', body)
      commit('setWaterlevels', body)
    },
    async computeClimate({ commit }, payload) {
      const apiUrl = process.env.VUE_APP_API_URI

      // only store the waypoints
      const climate = payload
      commit('setClimate', payload)

      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ climate })
      }
      const resp = await fetch(`${apiUrl}/climate`, requestOptions)
      const body = await resp.json()
      console.log('climateResults', body)
      commit('setClimateResults', body)
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
    setPlay(state, payload) {
      state.play = payload
    },
    setCurrentTime(state, payload) {
      state.currentTime = payload
    },
    setProgress(state, payload) {
      state.progress = payload
    },
    setRoute(state, payload) {
      state.route = payload
    },
    setWaterlevels(state, payload) {
      state.waterlevels = payload
      state.waterlevelBuffers = buffer(state.waterlevels, 500, {
        units: 'meters'
      })
    },
    setClimate(state, payload) {
      state.climate = payload
    },
    setClimateResults(state, payload) {
      const waterlevels = { ...payload }
      waterlevels.features = waterlevels.features.filter(
        feature => feature.properties.waterlevel
      )
      state.waterlevels = waterlevels
      state.waterlevelBuffers = buffer(state.waterlevels, 500, {
        units: 'meters'
      })

      const bathymetry = { ...payload }
      bathymetry.features = bathymetry.features.filter(
        feature => feature.properties.nap_p50
      )
      state.bathymetry = bathymetry
      state.bathymetryBuffers = buffer(state.bathymetry, 500, {
        units: 'meters'
      })

      const velocities = { ...payload }
      velocities.features = velocities.features.filter(
        feature => feature.properties.velocity
      )
      state.velocities = velocities
    },
    setChartTripDuration(state, payload) {
      state.chartTripDuration = payload
    },
    setChartDurationBreakdown(state, payload) {
      state.chartDurationBreakdown = payload
    },
    setChartTrips(state, payload) {
      state.chartTrips = payload
    },
    setSites(state, payload) {
      state.sites = payload
    },
    setFleet(state, payload) {
      // expects a list of selected ships
      state.fleet = payload
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
          cargo_type: 'Dry Bulk',
          capacity: 10000,
          level: 10000,
          loading_rate: 200,
          loading_rate_variation: 100
        },
        Container: {
          name: feature.properties.n,
          cargo_type: 'Container',
          capacity: 1000,
          level: 1000,
          loading_rate: 20,
          loading_rate_variation: 10
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
