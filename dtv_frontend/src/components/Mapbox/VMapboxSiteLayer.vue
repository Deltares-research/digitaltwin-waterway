<script>
import { mapState } from 'vuex'
export default {
  inject: ['getMap'],
  props: ['sites'],
  data () {
    return {
    }
  },
  render () {
    return null
  },
  computed: mapState(['route']),
  methods: {
    deferredMountedTo () {
      this.map = this.getMap()
      this.addSites()
    },
    addSites () {
      // TODO: get route for sites
      this.map.addSource('dtv-edges', {
        type: 'vector',
        url: 'mapbox://siggyf.dtv-edges'
      })
      console.log('route', this.route)
      this.map.addLayer({
        id: 'edge-highlight',
        type: 'line',
        source: 'dtv-edges',
        'source-layer': 'dtv-edges',
        layout: {
        },
        paint: {
          'line-color': 'hsla(301, 98%, 46%, 0.8)',
          'line-width': 2
        },
        filter: [
          'all',
          ['in', 'e_0', ...this.route],
          ['in', 'e_1', ...this.route]
        ]
      })
      this.map.addLayer({
        id: 'sites',
        type: 'circle',
        source: {
          type: 'geojson',
          data: this.sites
        },
        paint: {
          'circle-opacity': 0.9,
          'circle-color': '#C76C34'
        }
      })
    }
  }
}
</script>
