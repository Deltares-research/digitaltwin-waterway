<template>
  <v-mapbox
    id="map"
    ref="map"
    :zoom="8"
    :center="[4, 52]"
    :access-token="mapboxAccessToken"
    :preserve-drawing-buffer="true"
    map-style="mapbox://styles/siggyf/cl1tbrgu8000l14pk5x8jgbyg"
    @mb-load="publishMap"
    :logoPosition="'bottom-right'"
    :trackResize="'false'"
  >
    <v-mapbox-ships-layer
      v-if="features.length > 0"
      ref="shipsLayer"
      :tStart="results.env.epoch"
      :tStop="results.env.now"
      :results="results"
      :play="play"
      :progress="progress"
      @progressChange="onProgressChange"
      @end="onAnimationEnd"
    />
    <!-- :progress="progress" -->
    <v-mapbox-site-layer />
    <v-mapbox-climate-layer />
    <v-mapbox-navigation-control :options="{ visualizePitch: true }" position="bottom-right" />
  </v-mapbox>
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import VMapboxSiteLayer from './Mapbox/VMapboxSiteLayer'
import VMapboxShipsLayer from './Mapbox/VMapboxShipsLayer'
import VMapboxClimateLayer from './Mapbox/VMapboxClimateLayer'
import _ from 'lodash'

export default {
  inject: ['bus'],
  components: {
    VMapboxSiteLayer,
    VMapboxShipsLayer,
    VMapboxClimateLayer
  },
  computed: {
    ...mapState(['results', 'sites', 'play', 'progress']),
    features() {
      return _.get(this.results, 'log.features', [])
    }
  },
  data() {
    return {
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN
    }
  },
  methods: {
    ...mapMutations(['setCurrentTime', 'setProgress', 'setPlay']),
    // TODO: add comment about devtools
    onProgressChange: _.throttle(function ({ time, progress }) {
      this.setCurrentTime(time)
      this.setProgress(progress)
    }, 250),
    onAnimationEnd() {
      this.setPlay(true)
    },
    publishMap(event) {
      // emit over the event bus
      const map = event.target
      this.bus.emit('map', map)
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
