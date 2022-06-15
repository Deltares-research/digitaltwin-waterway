<script>
import { mapFields } from 'vuex-map-fields'
export default {
  inject: ['getMap'],
  props: ['climate'],
  data() {
    return {
      // only used for hovering
      hoverEdge: null
    }
  },
  render() {
    return null
  },
  computed: {
    ...mapFields(['waterlevels', 'velocities'])
  },
  watch: {
    waterlevels() {
      const map = this.getMap()
      console.log('updatting', this.waterlevels, this.getMap())
      const waterlevelSource = map.getSource('dtv-waterlevels')
      waterlevelSource.setData(this.waterlevels)
    }
  },
  methods: {
    deferredMountedTo() {
      this.addWaterlevels()
      // this.addVelocites()
    },
    addWaterlevels() {
      const map = this.getMap()
      map.addSource('dtv-waterlevels', {
        type: 'geojson',
        data: this.waterlevels
      })
      map.addLayer({
        id: 'edge-waterlevels',
        type: 'line',
        source: 'dtv-waterlevels',
        layout: {},
        paint: {
          'line-color': 'hsla(320, 80%, 50%, 0.5)',
          'line-width': ['get', 'waterlevel']
        }
      })
    }
  }
}
</script>
