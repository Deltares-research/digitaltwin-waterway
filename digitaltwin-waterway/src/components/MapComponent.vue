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
    <v-mapbox-ships-layer v-if="this.features.length > 0" />
    <v-mapbox-site-layer v-if="this.sites.features" />
    <v-mapbox-navigation-control
      :options="{ visualizePitch: true }"
      position="bottom-right"
    />
  </v-mapbox>
</template>

<script>
import { mapState } from 'vuex'
import VMapboxSiteLayer from './Mapbox/VMapboxSiteLayer'
import VMapboxShipsLayer from './Mapbox/VMapboxShipsLayer'
import _ from 'lodash'

export default {
  components: {
    VMapboxSiteLayer,
    VMapboxShipsLayer
  },
  computed: {
    ...mapState(['results', 'sites']),
    features () {
      return _.get(this.results, 'equipment.features', [])
    }
  },
  data () {
    return {
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      map: null
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
