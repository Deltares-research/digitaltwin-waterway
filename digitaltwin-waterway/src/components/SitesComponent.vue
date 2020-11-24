<template>
  <div>
    <h2> Sites </h2>
    <v-card v-for="site in sites.features" :key="site.id">
      <v-card-title>{{ site.properties.name }}</v-card-title>
      {{ site }}
    </v-card>
  </div>
</template>

<script>
import { mapActions, mapState } from 'vuex'

export default {
  data () {
    return {
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      draw: {}
    }
  },
  mounted () {
    this.fetchSites()
  },
  computed: {
    ...mapState(['sites'])
  },
  methods: {
    ...mapActions(['fetchSites'])
  }
}

</script>
