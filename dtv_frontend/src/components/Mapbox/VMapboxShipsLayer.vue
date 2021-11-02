<template>
  <div />
</template>

<script>
import * as turf from '@turf/turf'
import Vue from 'vue'
import mapboxgl from 'mapbox-gl'
import _ from 'lodash'
import ShipIcon from '@/components/ShipIcon.vue'
import * as d3 from 'd3'

const ShipIconClass = Vue.extend(ShipIcon)

export default {
  inject: ['getMap'],
  props: {
    tStart: {
      type: Number,
      required: true
    },
    tStop: {
      type: Number,
      required: true
    },
    results: {
      type: Object,
      required: true
    },
    sites: {
      type: Object,
      required: true
    },
    play: {
      type: Boolean,
      required: true
    },
    progress: {
      type: Number,
      default: 0
    },
    // run for n miliseconds
    duration: {
      type: Number,
      default: 240000
    }
  },
  data () {
    return {
      markers: {},
      initialized: false,
      startTime: null,
      internalProgress: 0,
      persistedProgress: 0
    }
  },
  watch: {
    play () {
      if (this.play) {
        this.start()
      }
    },
    progress (value) {
      if (!this.play) {
        this.startTime = 0
        this.persistedProgress = value
        this.internalProgress = 0

        this.animate()
      }
    },
    totalProgress () {
      this.moveShips()
    }
  },
  computed: {
    ships () {
      const ships = _.filter(
        _.get(this.results, 'log.features'),
        feature => (
          feature.properties['Actor type'] === 'Ship' &&
          ['Load request', 'Unload request', 'Sailing'].includes(feature.properties.Name)
        )
      )
      return ships
    },
    totalProgress () {
      return this.persistedProgress + this.internalProgress
    },
    timeScale () {
      return d3.scaleLinear()
        .domain([0, 1])
        .range([this.tStart, this.tStop])
    }
  },
  mounted () {
    this.map = this.getMap()
    this.addTrajectory()
  },
  methods: {
    deferredMountedTo () {
      this.map = this.getMap()
      this.addTrajectory()
    },
    clearMarkers () {
      Object.entries(this.markers).forEach(([key, marker]) => {
        marker.mapboxMarker.remove()
        this.$destroy(marker)
        delete this.markers[key]
      })
    },
    createMarker (ship) {
      const featId = ship.id
      const el = document.createElement('div')
      const child = document.createElement('div')

      el.appendChild(child)

      const mapboxMarker = new mapboxgl.Marker(el)
      const shipInfo = this.results.config.fleet.find(({ properties }) => properties.name === ship.properties.Actor)

      // create Vue component & mount to div
      const marker = new ShipIconClass({
        propsData: {
          mapboxMarker,
          shipImage: shipInfo.properties.image
        }
      }).$mount(child)

      const node = marker.$createElement('div', [featId])

      marker.$slots.default = [node]
      marker.$mount(child)

      // set to starting location
      const start = ship.geometry.type === 'Point' ? ship.geometry.coordinates : ship.geometry.coordinates[0]

      mapboxMarker.setLngLat(start)
      mapboxMarker.addTo(this.map)
      this.markers[featId] = marker
    },
    animate (timestamp) {
      if (!this.play) {
        // add internalProgress to the persistedProgress to make that the new starting point
        // when animation starts again
        this.persistedProgress = this.persistedProgress + this.internalProgress
        // reset internalProgress because that's included in the persistedProgress now
        this.internalProgress = 0
        this.startTime = null

        this.$emit('start')

        return
      }

      if (!this.startTime) {
        this.startTime = timestamp
      }

      const duration = timestamp - this.startTime

      // convert time-based values to progress in a range from 0 to 1
      this.internalProgress = duration / this.duration

      if (this.totalProgress >= 1) {
        this.$emit('end')

        return
      }

      requestAnimationFrame(this.animate)
    },
    start () {
      requestAnimationFrame(this.animate)
    },
    addTrajectory (id, coordinates) {
      const sourceId = `trajectory-source-${id}`
      const layerId = `trajectory-layer-${id}`

      if (!id || this.map.getSource(sourceId)) return

      this.map.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates
          }
        }
      })

      this.map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#00FFFF',
          'line-width': 2,
          'line-opacity': 0.1
        }
      })
    },
    createShips () {
      if (!this.initialized) {
        this.clearMarkers()

        this.ships.forEach(ship => {
          /* create and remember marker */
          this.createMarker(ship)
        })

        this.initialized = true
      }
    },
    moveShips () {
      this.createShips()

      // get current progress as time on timescale
      const tNow = this.timeScale(this.totalProgress)

      // emit progress & tNow when ships animate
      this.$emit('progressChange', {
        progress: this.totalProgress,
        time: tNow
      })

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
            this.markers[ship.id].mapboxMarker.setLngLat(along.geometry.coordinates)
            this.markers[ship.id].mapboxMarker.addTo(this.map)
          } else if (ship.properties.Name === 'Load request') {
            this.markers[ship.id].mapboxMarker.setLngLat(ship.geometry.coordinates)
            this.markers[ship.id].progress = fraction * 100
            this.markers[ship.id].mapboxMarker.addTo(this.map)
          } else if (ship.properties.Name === 'Unload request') {
            this.markers[ship.id].mapboxMarker.setLngLat(ship.geometry.coordinates)
            this.markers[ship.id].progress = 100 - (fraction * 100)
            this.markers[ship.id].mapboxMarker.addTo(this.map)
          }

          this.addTrajectory(ship.id, ship.geometry.coordinates)
        } else {
          this.markers[ship.id].mapboxMarker.remove()
        }
      })
    }
  }
}
</script>
