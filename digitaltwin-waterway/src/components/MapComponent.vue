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
export default {
  mounted () {
    this.map = this.$refs.map.map
    this.marker = new mapboxgl.Marker()
    this.map.on('load', () => {
      this.addSites()
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
        if (this.features.length > 0) {
          const options = { units: 'kilometers' }
          let points = this.results.path.features.map(feat => {
            return _.get(feat, 'geometry.coordinates')
          })
          points = points.flat()
          this.trajectory = turf.lineString(points)
          this.trajectoryLength = turf.length(this.trajectory, options)
          this.addTrajectory()
          // Start the animation.
          requestAnimationFrame(this.animateMarker)
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
      marker: null,
      count: 0,
      trajectory: null,
      trajectoryLength: 0
    }
  },
  methods: {
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
      this.marker.setLngLat(coordinates)
      this.marker.addTo(this.map)

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
