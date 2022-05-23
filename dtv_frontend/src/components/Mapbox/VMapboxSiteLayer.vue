<script>
import { mapFields } from 'vuex-map-fields'
import { mapGetters, mapMutations } from 'vuex'
export default {
  inject: ['getMap'],
  props: ['sites'],
  data() {
    return {
      // only used for hovering
      hoverWaypoint: null
    }
  },
  render() {
    return null
  },
  computed: {
    ...mapFields(['route', 'waypoints']),
    ...mapGetters(['unit'])
  },
  methods: {
    ...mapMutations(['addWaypoint']),
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
      this.map.on('mousemove', 'node-hover', (e) => {
        if (e.features.length > 0) {
          this.map.getCanvas().style.cursor = 'pointer'
          const feature = e.features[0]
          // store as active node
          this.hoverWaypoint = feature
          // nover waypoints
          const waypoints = [...this.waypoints, this.hoverWaypoint]
          const waypointNodes = waypoints.map((feature) => feature.properties.n)
          this.map.setFilter('node-highlight', ['in', 'n', ...waypointNodes])
        }
      })
      this.map.on('mouseleave', 'node-hover', () => {
        this.map.getCanvas().style.cursor = ''
        this.hoverWaypoint = null
        const waypointNodes = this.waypoints.map(
          (feature) => feature.properties.n
        )

        this.map.setFilter('node-highlight', ['in', 'n', ...waypointNodes])
      })
      this.map.on('click', 'node-hover', (e) => {
        if (!e.features || e.features.length < 1) {
          // no features available
          return
        }
        const feature = e.features[0]
        // TODO: check if this works
        this.addWaypoint(feature)
      })
    }
  }
}
</script>
