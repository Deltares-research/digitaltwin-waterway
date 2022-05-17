<template>
<div>
  <v-card class="mb-4">
    <v-card-title>
      Cargo type
    </v-card-title>
    <v-card-text>
      <v-select :items="cargoTypes" v-model="cargoType"></v-select>
    </v-card-text>
  </v-card>
  <div v-if="cargoType">
    <v-card v-for="site in sitesForCargo" :key="site.id" outlined class="mb-4">
      <v-card-title class="mb-4">
        {{ site.properties.name }}
        <v-spacer />
        <v-avatar size="20px">
          <img :src="harborIcon">
        </v-avatar>
      </v-card-title>
      <v-card-text>
        <v-slider
          v-if="site.properties.name === 'Maasvlakte'"

          :step="step"
          inverse-label
          :min="0"
          :max="maxCapacity"
          :label="unit"
          thumb-label="always"

          v-model="site.properties.level"
          ></v-slider>
        <v-slider
          v-if="site.properties.name === 'BCTN'"
          disabled
          :step="step"
          inverse-label
          :min="0"
          :max="maxCapacity"
          :label="unit"
          thumb-label="always"

          v-model="site.properties.level"
          ></v-slider>
      </v-card-text>
      <v-card-actions>
        <v-chip v-if="site.properties.loading_rate">Loading rate: {{ site.properties.loading_rate }}</v-chip>
        <v-chip>Capacity: {{ site.properties.capacity }}</v-chip>
        <v-chip>Level: {{ site.properties.level }}</v-chip>
        <v-chip>Cargo: {{ site.properties.cargo }}</v-chip>
      </v-card-actions>
    </v-card>
  </div>

</div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'
import harborIcon from '@mapbox/maki/icons/harbor-11.svg'
import { mapFields } from 'vuex-map-fields'

export default {
  data() {
    return {
      cargoTypes: ['Dry Bulk', 'Container'],
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      harborIcon,
      draw: {}
    }
  },
  computed: {
    ...mapState(['sites']),
    ...mapGetters(['unit']),
    ...mapFields([
      'cargoType'
    ]),
    sitesForCargo() {
      let sites = this.sites.features
      if (this.cargoType) {
        sites = this.sites.features.filter(site => site.properties.cargo === this.cargoType)
      }
      return sites
    },
    maxCapacity() {
      let maxCapacity = 1000
      if (this.unit === 'TEU') {
        maxCapacity = 1e4
      } else if (this.unit === 'Tonne') {
        maxCapacity = 1e3
      }
      return maxCapacity
    },
    step() {
      let step = 10
      if (this.unit === 'TEU') {
        step = 10
      } else if (this.unit === 'Tonne') {
        step = 100
      }
      return step
    }

  }
}
</script>
