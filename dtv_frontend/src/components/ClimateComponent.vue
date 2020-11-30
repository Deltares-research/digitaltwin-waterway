<template>
<div>
  <v-card>
    <v-card-title class="mb-3">
      Climate
    </v-card-title>
    <v-card-text>
      <v-slider
        :step="500"
        inverse-label
        :min="0"
        :max="30000"
        label="Rhine discharge"
        thumb-label="always"
        v-model="rhine"
      ></v-slider>
      <v-slider
        inverse-label
        :min="0"
        :max="600"
        disabled
        label="Nijmegen waterlevel"
        thumb-label="always"
        v-model="nijmegen"
      ></v-slider>
      <v-slider
        inverse-label
        :min="0"
        :max="600"
        disabled
        label="Kiel waterlevel"
        thumb-label="always"
        v-model="kiel"
      ></v-slider>
      <v-slider
        inverse-label
        :min="0"
        :max="600"
        disabled
        label="Neuss waterlevel"
        thumb-label="always"
        v-model="neuss"
      ></v-slider>
    </v-card-text>
  </v-card>
</div>
</template>
<script>
export default {
  name: 'ClimateComponent',
  data () {
    return {
      rhine: 0
    }
  },
  computed: {
    nijmegen () {
      return this.rhine / 70
    },
    kiel () {
      return this.rhine / 50
    },
    neuss () {
      return this.rhine / 80
    }

  }
}
</script>
