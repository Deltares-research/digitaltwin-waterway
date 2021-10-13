<template>
  <v-mapbox
    id="map"
    ref="map"
    :zoom="5"
    :center="[6, 50]"
    :access-token="mapboxAccessToken"
    :preserve-drawing-buffer="true"
    map-style="mapbox://styles/global-data-viewer/cjtss3jfb05w71fmra13u4qqm"
    :logoPosition="'bottom-right'"
    :trackResize="'false'"
  >
    <v-mapbox-ships-layer
      v-if="features.length > 0"
      :tStart="results.env.epoch"
      :tStop="results.env.now"
      :results="results"
      :sites="sites"
      :play="play"
      @shipStateChange="onShipStateChange"
      @timeChange="onTimeChange"
    />
    <v-mapbox-site-layer v-if="sites.features" :sites="sites" />
    <v-mapbox-navigation-control
      :options="{ visualizePitch: true }"
      position="bottom-right"
    />
  </v-mapbox>
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import VMapboxSiteLayer from './Mapbox/VMapboxSiteLayer'
import VMapboxShipsLayer from './Mapbox/VMapboxShipsLayer'
import _ from 'lodash'

export default {
  components: {
    VMapboxSiteLayer,
    VMapboxShipsLayer
  },
  computed: {
    ...mapState(['results', 'sites', 'play']),
    features () {
      return _.get(this.results, 'log.features', [])
    }
  },
  data () {
    return {
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      map: null
    }
  },
  methods: {
    ...mapMutations(['setPlay', 'setShipState', 'setCurrentTime']),
    onShipStateChange (value) {
      this.setShipState(value)
    },
    onTimeChange: _.throttle(function (value) {
      this.setCurrentTime(value)
    }, 500)
  }
}
</script>

<style>
#map {
  width: 100%;
  height: 100%;
}
</style>
