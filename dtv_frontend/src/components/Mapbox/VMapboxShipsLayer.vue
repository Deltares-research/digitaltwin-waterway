<template>
  <div />
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import * as turf from '@turf/turf'
import Vue from 'vue'
import mapboxgl from 'mapbox-gl'
import _ from 'lodash'
import ShipIcon from '@/components/ShipIcon.vue'

const ShipIconClass = Vue.extend(ShipIcon)

export default {
  inject: ['getMap'],
  props: {
  },
  watch: {
    play: {
      handler () {
        if (this.play) {
          this.startSailing()
        }
      }
    }
  },
  data () {
    return {
      markers: {},
      count: 0,
      trajectory: null,
      trajectoryLength: 0,
      cargo: 0,
      distance: 0,
      forward: true,
      maxCargo: 0
    }
  },
  computed: {
    ...mapState(['results', 'sites']),
    play: {
      get () { return this.$store.state.play },
      set (value) { this.setPlay(value) }
    },
    shipState: {
      get () { return this.$store.state.shipState },
      set (value) { this.setShipState(value) }
    }
  },
  mounted () {
    this.map = this.getMap()
    this.setFeatures()
    this.addTrajectory()
    this.createMarker()
  },
  methods: {
    ...mapMutations(['setPlay', 'setShipState']),
    setFeatures () {
      const options = { units: 'kilometers' }
      let points = this.results.path.features.map(feat => {
        return _.get(feat, 'geometry.coordinates')
      })
      points = points.flat()
      this.trajectory = turf.lineString(points)
      this.trajectoryLength = turf.length(this.trajectory, options)
      const cargo = this.results.equipment.features.map(feat => parseFloat(feat.properties.Value))
      this.maxCargo = Math.max(...cargo)
    },
    createMarker () {
      const featId = 'ship1'
      const el = document.createElement('div')
      const child = document.createElement('div')
      el.appendChild(child)

      const mapboxMarker = new mapboxgl.Marker(el)

      const marker = new ShipIconClass({
        propsData: {
          mapboxMarker
        }
      }).$mount(child)
      const node = marker.$createElement('div', [featId])
      marker.$slots.default = [node]
      marker.$mount(child)
      this.markers.[featId] = marker
    },
    animateMarker (timestamp) {
      if (!this.play) {
        return
      }
      const options = { units: 'kilometers' }
      let along = this.count
      if (!this.forward) {
        along = this.trajectoryLength - this.count
      }
      const location = turf.along(this.trajectory, along, options)
      const coordinates = _.get(location, 'geometry.coordinates')
      const marker = _.get(this.markers, 'ship1.mapboxMarker')
      marker.setLngLat(coordinates)
      marker.addTo(this.map)

      this.count += 10

      if (this.count > this.trajectoryLength) {
        this.shipState += 1
        this.startSailing()
      } else {
        // Request the next frame of the animation.
        requestAnimationFrame(this.animateMarker)
      }
    },
    animateCargo () {
      // Animate the loading of the cargo
      if (!this.play) {
        return
      }
      this.count += 5
      const marker = _.get(this.markers, 'ship1')
      const progress = 100 - (100 * this.cargo[this.count] / this.maxCargo)
      console.log(marker, this.cargo[this.count], this.maxCargo, progress)
      marker.progress = progress
      if (this.count > this.cargo.length) {
        this.shipState += 1
        this.startSailing()
      } else {
        // Request the next frame of the animation.
        requestAnimationFrame(this.animateCargo)
      }
    },
    startSailing () {
      // Get the data to either visualize cargo or sailing of the ship
      if (!this.play) {
        return
      }
      const features = _.get(this.results, 'equipment.features')
      const origin = features.find(feat => parseInt(feat.id) === this.shipState)
      const destination = features.find(feat => parseInt(feat.id) === this.shipState + 1) || origin

      // Set the marker ot the origin position of this trip (mostly important for first)
      // session, where cargo is loaded and not the marker moved.
      const marker = _.get(this.markers, 'ship1.mapboxMarker')
      marker.setLngLat(origin.geometry.coordinates)
      marker.addTo(this.map)

      // Calculate distance from origin to destination. If no distance, then
      // the cargo should be visualized. If there is a distance, visualize the trip/
      // TODO: Check origin and destination per session with the true orig and destination (otherwise )
      // we only have one way trips..
      this.currentDistance = turf.distance(origin.geometry.coordinates, destination.geometry.coordinates, { units: 'kilometers' })
      this.cargo = _.range([origin.properties.Value], destination.properties.Value, [10])
      this.count = 0
      console.log(this.currentDistance, this.cargo)
      if (this.currentDistance === 0) {
        requestAnimationFrame(this.animateCargo)
      } else {
        this.forward = turf.distance(origin.geometry.coordinates, _.get(this.sites, 'features[0].geometry.coordinates')) === 0
        requestAnimationFrame(this.animateMarker)
      }
    },
    addTrajectory () {
      this.map.addLayer({
        id: 'trajectory',
        type: 'line',
        source: {
          type: 'geojson',
          data: this.results.path
        },
        paint: {
          'line-color': 'red'
        }
      })
    }
  }
}
</script>
