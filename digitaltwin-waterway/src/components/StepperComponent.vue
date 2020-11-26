<template>
  <v-stepper
    v-model="stepper"
    vertical
    class="stepper"
  >
    <v-stepper-step
      :complete="stepper > 1"
      step="1"
      @click="stepper = 1"
    >
      Sites
      <small>Selection location A to B</small>
    </v-stepper-step>

    <v-stepper-content step="1">
      <sites-component></sites-component>
    </v-stepper-content>

    <v-stepper-step
      :complete="stepper > 2"
      step="2"
      @click="stepper = 2"
    >
      Fleet
      <small>Selection of ships within a fleet</small>
    </v-stepper-step>

    <v-stepper-content step="2" class="fleets">
      <fleet-component />
      <v-btn
        color="primary"
        @click="stepper = 3"
      >
        Continue
      </v-btn>
      <v-btn
        text
        @click="stepper = 2"
      >
        Back
      </v-btn>
    </v-stepper-content>

    <v-stepper-step
      :complete="stepper > 3"
      step="3"
      @click="stepper = 3"
    >
      Climate
      <small>Set climate conditions</small>
    </v-stepper-step>

    <v-stepper-content step="3">
      <climate-component />
      <v-btn
        color="primary"
        @click="stepper = 4"
      >
        Start sailing
      </v-btn>
      <v-btn
        text
        @click="stepper = 2"
      >
        Back
      </v-btn>
    </v-stepper-content>
    <v-stepper-step
      :complete="stepper > 4"
      step="4"
      @click="stepper = 4"
    >
      Results
      <small>charts and visualisations</small>
    </v-stepper-step>
    <v-stepper-content step="4">
      <result-component></result-component>
    </v-stepper-content>
  </v-stepper>
</template>

<script>
import FleetComponent from './FleetComponent'
import SitesComponent from './SitesComponent'
import ClimateComponent from './ClimateComponent'
import ResultComponent from './ResultComponent'

export default {
  data () {
    return {
      stepper: 1
    }
  },
  components: {
    FleetComponent,
    SitesComponent,
    ClimateComponent,
    ResultComponent
  },
  methods: {
  }
}
</script>

<style>
.stepper {
  max-height: 100%;
  height: 100%;
}

.fleets {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
