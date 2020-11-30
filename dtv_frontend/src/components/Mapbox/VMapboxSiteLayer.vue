<template>
  <div />
</template>

<script>
import { mapState } from 'vuex'

export default {
  inject: ['getMap'],
  props: {
  },
  data () {
    return {
    }
  },
  computed: {
    ...mapState(['sites'])
  },
  methods: {
    deferredMountedTo () {
      this.map = this.getMap()
      this.addSites()
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
    }
  }
}
</script>
