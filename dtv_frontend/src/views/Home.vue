<template>
<v-row class="main-row" no-gutters>
  <v-col class="pa-3 main-row" cols="12" md="7">
    <stepper-component />
  </v-col>
  <v-col class="pa-0" cols="12" md="5">
    <map-component />
  </v-col>
</v-row>
</template>
<script>
import { mapActions } from 'vuex'
import MapComponent from '@/components/MapComponent'
import StepperComponent from '@/components/StepperComponent'

export default {
  name: 'Home',
  components: {
    MapComponent,
    StepperComponent
  },
  created () {
    this.fetchSites()
  },
  methods: {
    ...mapActions(['fetchSites'])
  }
}
</script>
