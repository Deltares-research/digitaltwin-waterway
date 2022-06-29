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
    ...mapFields([
      'waterlevels',
      'waterlevelBuffers',
      'bathymetry',
      'bathymetryBuffers',
      'velocities'
    ])
  },
  watch: {
    // update sources when data changes
    waterlevels() {
      const map = this.getMap()
      if (!map) {
        return
      }
      const waterlevelSource = map.getSource('dtv-waterlevels')
      if (!waterlevelSource) {
        return
      }
      waterlevelSource.setData(this.waterlevels)
    },
    waterlevelBuffers() {
      const map = this.getMap()
      if (!map) {
        return
      }
      const waterlevelBufferSource = map.getSource('dtv-waterlevel-buffers')
      if (!waterlevelBufferSource) {
        return
      }
      waterlevelBufferSource.setData(this.waterlevelBuffers)
    },
    bathymetry() {
      const map = this.getMap()
      if (!map) {
        return
      }
      const bathymetrySource = map.getSource('dtv-bathymetry')
      if (!bathymetrySource) {
        return
      }
      bathymetrySource.setData(this.bathymetry)
    },
    bathymetryBuffers() {
      const map = this.getMap()
      if (!map) {
        return
      }
      const bathymetryBufferSource = map.getSource('dtv-bathymetry-buffers')
      if (!bathymetryBufferSource) {
        return
      }
      bathymetryBufferSource.setData(this.bathymetryBuffers)
    },
    velocities() {
      const map = this.getMap()
      if (!map) {
        return
      }
      const velocitySource = map.getSource('dtv-velocities')
      if (!velocitySource) {
        return
      }
      velocitySource.setData(this.velocities)
    }
  },
  methods: {
    deferredMountedTo() {
      this.addClimate()
      // this.addVelocites()
    },
    addSources(map) {
      map.addSource('dtv-waterlevels', {
        type: 'geojson',
        data: this.waterlevels
      })
      map.addSource('dtv-waterlevel-buffers', {
        type: 'geojson',
        data: this.waterlevelBuffers
      })
      map.addSource('dtv-bathymetry', {
        type: 'geojson',
        data: this.bathymetry
      })
      map.addSource('dtv-bathymetry-buffers', {
        type: 'geojson',
        data: this.bathymetryBuffers
      })
      map.addSource('dtv-velocities', {
        type: 'geojson',
        data: this.velocities
      })
    },
    addLayers(map) {
      const velocityMultiplier = 3
      map.addLayer({
        id: 'edge-velocities',
        type: 'line',
        source: 'dtv-velocities',
        layout: {},
        paint: {
          'line-color': [
            'interpolate',
            ['linear'],
            ['get', 'velocity'],
            0,
            'hsla(320, 80%, 50%, 0.5)',
            2,
            'hsla(180, 80%, 50%, 0.5)'
          ],
          'line-width': ['*', ['get', 'velocity'], velocityMultiplier]
        }
      })

      // const elevationBase = 1000
      const elevationMultiplier = 100
      map.addLayer({
        id: 'edge-waterdepth-buffers',
        type: 'fill-extrusion',
        source: 'dtv-waterlevel-buffers',
        layout: {},
        paint: {
          'fill-extrusion-height': [
            '-',
            ['*', ['get', 'waterlevel'], elevationMultiplier],
            ['*', ['get', 'nap_p5'], elevationMultiplier]
          ],
          'fill-extrusion-color': 'hsl(180, 0%, 50%)',
          'fill-extrusion-opacity': 0.3
        }
      })
    },
    addClimate() {
      const map = this.getMap()
      this.addSources(map)
      this.addLayers(map)
    }
  }
}
</script>
