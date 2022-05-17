<script>
import { mapState } from 'vuex'
export default {
  inject: ['getMap'],
  props: ['sites'],
  data() {
    return {
      waypoints: ['8865973', '22638188'],
      waypointHover: null
    }
  },
  render() {
    return null
  },
  computed: mapState(['route']),
  methods: {
    deferredMountedTo() {
      this.map = this.getMap()
      this.addSites()
    },
    addSites() {
      // TODO: get route for sites
      this.map.addSource('dtv-edges', {
        type: 'vector',
        url: 'mapbox://siggyf.dtv-edges'
      })
      this.map.addSource('dtv-nodes', {
        type: 'vector',
        url: 'mapbox://siggyf.dtv-nodes'
      })
      console.log('route', this.route)
      this.map.addLayer({
        id: 'edge-highlight',
        type: 'line',
        source: 'dtv-edges',
        'source-layer': 'dtv-edges',
        layout: {},
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
      /* use this layer to capture hovers */
      this.map.addLayer({
        id: 'node-hover',
        type: 'circle',
        source: 'dtv-nodes',
        'source-layer': 'dtv-nodes',
        layout: {},
        paint: {
          'circle-opacity': 0
        }
      })
      /* this layer shows active points */
      this.map.addLayer({
        id: 'node-highlight',
        type: 'circle',
        source: 'dtv-nodes',
        'source-layer': 'dtv-nodes',
        layout: {},
        paint: {
          'circle-color': 'hsla(301, 98%, 46%, 0.8)',
          'circle-stroke-color': 'white',
          'circle-stroke-width': 2
        },
        filter: ['in', 'n', ...this.waypoints]
      })
      this.map.addLayer({
        id: 'sites',
        type: 'circle',
        source: {
          type: 'geojson',
          data: this.sites
        },
        paint: {
          'circle-opacity': 0.3,
          'circle-stroke-width': 0,
          'circle-color': 'hsla(301, 98%, 46%, 0.8)'
        }
      })
      this.map.on('mousemove', 'node-hover', e => {
        if (e.features.length > 0) {
          this.map.getCanvas().style.cursor = 'pointer'
          const feature = e.features[0]
          const n = feature.properties.n
          this.waypointHover = n
          const waypoints = [...this.waypoints, this.waypointHover]
          console.log('waypoints', waypoints)
          this.map.setFilter('node-highlight', ['in', 'n', ...waypoints])
        }
      })
      this.map.on('mouseleave', 'node-hover', () => {
        this.map.getCanvas().style.cursor = ''
        this.waypointHover = null
        this.map.setFilter('node-highlight', ['in', 'n', ...this.waypoints])
      })
      this.map.on('click', 'node-hover', e => {
        console.log('click', e, e.features, e.features[0].properties.n)
      })
    }
  }
}
</script>
