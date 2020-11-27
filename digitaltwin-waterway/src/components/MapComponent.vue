<template>
  <v-mapbox
    id="map"
    ref="map"
    :access-token="mapboxAccessToken"
    :preserve-drawing-buffer="true"
    map-style="mapbox://styles/global-data-viewer/cjtss3jfb05w71fmra13u4qqm"
    :logoPosition="'bottom-right'"
    :trackResize="'false'"
  >
    <v-mapbox-navigation-control
      :options="{ visualizePitch: true }"
      position="bottom-right"
    />
  </v-mapbox>
</template>

<script>
import { mapState } from 'vuex'
import mapboxgl from 'mapbox-gl'
import _ from 'lodash'
import * as turf from '@turf/turf'
import Vue from 'vue'
import ShipIcon from '@/components/ShipIcon.vue'

const ShipIconClass = Vue.extend(ShipIcon)

export default {
  mounted () {
    this.map = this.$refs.map.map
    this.createMarker()
    this.map.on('load', () => {
      console.log('map loaded')
      this.addSites()
      this.addTrajectory()
      // Start the animation.
      requestAnimationFrame(this.animateMarker)
    })
  },
  computed: {
    ...mapState(['results', 'sites']),
    features () {
      return _.get(this.results, 'equipment.features', [])
    }
  },
  watch: {
    features: {
      handler () {
        console.log(this.features, this.features.length > 0)
        if (this.features.length > 0) {
          const options = { units: 'kilometers' }
          let points = this.results.path.features.map(feat => {
            return _.get(feat, 'geometry.coordinates')
          })
          points = points.flat()
          this.trajectory = turf.lineString(points)
          this.trajectoryLength = turf.length(this.trajectory, options)
        }
      },
      deep: true
    }
  },
  data () {
    return {
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      draw: {},
      map: null,
      markers: {},
      count: 0,
      trajectory: null,
      trajectoryLength: 0
    }
  },
  methods: {
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
    addSites () {
      this.map.addLayer({
        id: 'sites',
        type: 'circle',
        source: {
          type: 'geojson',
          data: this.sites
        },
        paint: {
          'circle-color': 'red'
        }
      })
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
    },
    animateMarker (timestamp) {
      // var radius = 20

      const options = { units: 'kilometers' }
      const location = turf.along(this.trajectory, this.count, options)
      const coordinates = _.get(location, 'geometry.coordinates')
      const marker = _.get(this.markers, 'ship1.mapboxMarker')
      marker.setLngLat(coordinates)
      marker.addTo(this.map)

      this.count += 1
      if (this.count > this.trajectoryLength) {
        this.count = 0
      }

      // Request the next frame of the animation.
      requestAnimationFrame(this.animateMarker)
    }
  }
}
</script>

<style>
#map {
  width: 100%;
  height: 100%;
}
</style>
