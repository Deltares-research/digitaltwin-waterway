<template>
<v-card>
  <h2> Sites </h2>
</v-card>
</template>

<script>
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
  methods: {
    fetchSites () {

    }
  }
}

</script>
