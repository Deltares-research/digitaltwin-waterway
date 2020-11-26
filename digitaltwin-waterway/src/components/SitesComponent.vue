<template>
  <div>
    <h2> Sites </h2>
    <v-card v-for="site in sites.features" :key="site.id">
      <v-card-title>{{ site.properties.name }}</v-card-title>
      <v-card-text>
        <v-slider
          hint="Cargo"
          :step="1000"
          thumb-label
          :min="0"
          :max="30000"
          v-model="site.properties.cargo"
        ></v-slider>
      </v-card-text>
      {{ site }}
    </v-card>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  data () {
    return {
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      draw: {}
    }
  },
  computed: {
    ...mapState(['sites'])
  }
}

</script>
