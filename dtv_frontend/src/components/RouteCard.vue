<template>
  <v-card class="mb-4">
    <v-card-title>
      Route information
      <v-spacer />
      <v-avatar size="20px">
        <img :src="markerIcon" />
      </v-avatar>
    </v-card-title>
    <v-list two-line>
      <v-list-item>
        <v-list-item-icon>
          <v-icon>mdi-ruler-square-compass</v-icon>
        </v-list-item-icon>

        <v-list-item-content>
          <v-list-item-title>{{formatNumber(route.properties.total_length_m / 1000) }}</v-list-item-title>
          <v-list-item-subtitle>Route length [km]</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <v-list-item>
        <v-list-item-icon>
          <v-icon>mdi-circle-medium</v-icon>
        </v-list-item-icon>

        <v-list-item-content>
          <v-list-item-title>{{ route.properties.n_edges }}</v-list-item-title>
          <v-list-item-subtitle># nodes</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <v-divider inset></v-divider>
      <v-list-item>
        <v-list-item-icon>
          <v-icon>mdi-bridge</v-icon>
        </v-list-item-icon>

        <v-list-item-content>
          <v-list-item-title>{{ structures.bridges }}</v-list-item-title>
          <v-list-item-subtitle># bridges</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-icon>
          <v-img :src="markerLock"></v-img>
        </v-list-item-icon>

        <v-list-item-content>
          <v-list-item-title>{{ structures.locks }}</v-list-item-title>
          <v-list-item-subtitle># locks</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item>
        <v-list-item-icon>
          <v-icon>mdi-flag</v-icon>
        </v-list-item-icon>

        <v-list-item-content>
          <v-list-item-title>{{ structures.structures }}</v-list-item-title>
          <v-list-item-subtitle># other structures</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
    <v-card-actions>
      <v-btn text @click="exportRoute">Export</v-btn>
    </v-card-actions>
  </v-card>
</template>
<script>
import markerIcon from '@mapbox/maki/icons/marker-11.svg'
import markerLock from '@mapbox/maki/icons/ferry-11.svg'

import { saveAs } from 'file-saver'
import { mapFields } from 'vuex-map-fields'

export default {
  data() {
    return {
      markerIcon,
      markerLock
    }
  },
  computed: {
    ...mapFields(['route']),
    structures() {
      const allStructures = this.route.features.filter(
        (feature) => feature.properties.structure
      )
      const bridges = allStructures.filter(
        (feature) => feature.properties.structure.structure_type === 'Bridge'
      )
      const locks = allStructures.filter(
        (feature) => feature.properties.structure.structure_type === 'Lock'
      )
      const structures = allStructures.filter(
        (feature) => feature.properties.structure.structure_type === 'Structure'
      )
      return {
        bridges: bridges.length,
        locks: locks.length,
        structures: structures.length
      }
    }
  },
  methods: {
    formatNumber(number) {
      return Intl.NumberFormat().format(number)
    },
    exportRoute() {
      var blob = new Blob([JSON.stringify(this.route)], {
        type: 'application/json;charset=utf-8'
      })
      saveAs(blob, 'route.geojson')
    }
  }
}
</script>
