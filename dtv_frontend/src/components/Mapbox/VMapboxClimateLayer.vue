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
    ...mapFields(['waterlevels', 'waterlevelBuffers', 'velocities'])
  },
  watch: {
    waterlevels() {
      const map = this.getMap()
      console.log('updatting', this.waterlevels, this.getMap())
      const waterlevelSource = map.getSource('dtv-waterlevels')
      waterlevelSource.setData(this.waterlevels)
    },
    waterlevelBuffers() {
      const map = this.getMap()
      const waterlevelBufferSource = map.getSource('dtv-waterlevel-buffers')
      waterlevelBufferSource.setData(this.waterlevelBuffers)
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
      map.addSource('dtv-waterlevel-buffers', {
        type: 'geojson',
        data: this.waterlevelBuffers
      })
      map.addLayer({
        id: 'edge-waterlevels',
        type: 'line',
        source: 'dtv-waterlevels',
        layout: {},
        paint: {
          'line-color': [
            'interpolate',
            ['linear'],
            ['get', 'waterlevel'],
            0,
            'hsla(320, 80%, 50%, 0.5)',
            20,
            'hsla(180, 80%, 50%, 0.5)'
          ],
          'line-width': 5
        }
      })
      map.addLayer({
        id: 'edge-waterlevel-buffers',
        type: 'fill-extrusion',
        source: 'dtv-waterlevel-buffers',
        layout: {},
        paint: {
          'fill-extrusion-height': ['*', ['get', 'waterlevel'], 100],
          'fill-extrusion-color': [
            'interpolate',
            ['linear'],
            ['get', 'waterlevel'],
            0,
            'hsla(320, 80%, 50%, 0.5)',
            20,
            'hsla(180, 80%, 50%, 0.5)'
          ],
          'fill-extrusion-opacity': 0.3
        }
      })
    }
  }
}
</script>
