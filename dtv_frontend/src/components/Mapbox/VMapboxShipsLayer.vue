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
import * as d3 from 'd3'

const ShipIconClass = Vue.extend(ShipIcon)

export default {
  inject: ['getMap'],
  props: ['tStart', 'tStop'],
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
      // Start time for animation
      start: null,
      // run for 30s
      duration: 30,
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
    },
    ships () {
      const ships = _.filter(
        _.get(this.results, 'log.features'),
        feature => (
          feature.properties['Actor type'] === 'Ship' &&
          ['Load', 'Sailing'].includes(feature.properties.Name)
        )
      )
      return ships
    }
  },
  mounted () {
    this.map = this.getMap()
  },
  methods: {
    ...mapMutations(['setPlay', 'setShipState']),
    clearMarkers () {
      Object.entries(this.markers).forEach(([key, marker]) => {
        marker.remove()
        delete this.markers[key]
      })
    },
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
    createMarker (ship) {
      const featId = ship.id
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

      /* set to starting location */
      const start = ship.geometry.type === 'Point' ? ship.geometry.coordinates : ship.geometry.coordinates[0]
      mapboxMarker.setLngLat(start)
      mapboxMarker.addTo(this.map)
      mapboxMarker.vueMarker = marker
      this.markers.[featId] = mapboxMarker
    },
    animate (timestamp) {
      if (this.start === null) {
        this.start = timestamp
      }

      if (timestamp > (this.start + (this.duration * 1000))) {
        this.play = false
        return
      }
      requestAnimationFrame(this.animate)
      // const elapsed = timestamp - start
      const timeScale = (
        d3.scaleLinear()
          .domain([this.start, this.start + this.duration * 1000])
          .range([this.tStart, this.tStop])
      )
      const tNow = timeScale(timestamp)
      // lookup ships
      // set state to what it should be
      this.ships.forEach(ship => {
        if (
          tNow >= ship.properties['Start Timestamp'] &&
          tNow < ship.properties['Stop Timestamp']
        ) {
          // animate ship
          const fraction = (
            (tNow - ship.properties['Start Timestamp']) /
            (ship.properties['Stop Timestamp'] - ship.properties['Start Timestamp'])
          )
          if (ship.properties.Name === 'Sailing') {
            const options = { units: 'kilometers' }
            const length = turf.length(ship.geometry, options)
            const along = turf.along(ship.geometry, length * fraction, options)
            this.markers[ship.id].setLngLat(along.geometry.coordinates)
            this.markers[ship.id].addTo(this.map)
          } else {
            this.markers[ship.id].vueMarker.progress = fraction * 100
            this.markers[ship.id].addTo(this.map)
          }
        } else {
          this.markers[ship.id].remove()
        }
      })
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

      this.start = null
      this.clearMarkers()

      /* clear markers */
      console.log('ships', this.ships)

      this.ships.forEach(ship => {
        /* create and remember marker */
        this.createMarker(ship)
      })

      requestAnimationFrame(this.animate)

      // Calculate distance from origin to destination. If no distance, then
      // the cargo should be visualized. If there is a distance, visualize the trip/
      // TODO: Check origin and destination per session with the true orig and destination (otherwise )
      // we only have one way trips..
      /*
      this.currentDistance = turf.distance(origin.geometry.coordinates, destination.geometry.coordinates, { units: 'kilometers' })
      this.cargo = _.range([origin.properties.Value], destination.properties.Value, [10])
      this.count = 0
      console.log(this.currentDistance, this.cargo)
      if (this.currentDistance === 0) {
      } else {
        this.forward = turf.distance(origin.geometry.coordinates, _.get(this.sites, 'features[0].geometry.coordinates')) === 0
        requestAnimationFrame(this.animateMarker)
      }
       */
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
