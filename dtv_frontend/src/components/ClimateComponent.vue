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
        label="Kaub waterlevel"
        thumb-label="always"
        v-model="kaub"
      ></v-slider>
      <v-slider
        inverse-label
        :min="0"
        :max="600"
        disabled
        label="Duisburg waterlevel"
        thumb-label="always"
        v-model="duisburg"
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
    kaub () {
      return this.rhine / 80
    },
    duisburg () {
      return this.rhine / 50
    }

  }
}
</script>
