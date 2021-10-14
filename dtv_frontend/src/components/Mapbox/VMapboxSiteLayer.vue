<template>
  <div />
</template>

<script>
export default {
  inject: ['getMap'],
  props: ['sites'],
  data () {
    return {
    }
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
          'circle-color': '#00FFFF'
        }
      })
    }
  }
}
</script>
