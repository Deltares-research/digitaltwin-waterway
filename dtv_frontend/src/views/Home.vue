<template>
  <v-row class="main-row" no-gutters>
    <v-col class="pa-3 main-row" cols="12" md="7">
      <stepper-component :map="map" />
    </v-col>
    <v-col class="pa-0" cols="12" md="5">
      <map-component @mb-load="setMap"></map-component>
    </v-col>
  </v-row>
</template>
<script>
import MapComponent from '@/components/MapComponent'
import StepperComponent from '@/components/StepperComponent'

export default {
  name: 'Home',
  data() {
    return {
      map: null
    }
  },
  components: {
    MapComponent,
    StepperComponent
  },
  created() {},
  methods: {
    setMap(e) {
      console.log('event', e)
      this.map = e.target
    }
  }
}
</script>
