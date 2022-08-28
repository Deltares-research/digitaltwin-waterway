<template>
  <v-stepper class="stepper" v-model="stepper">
    <v-stepper-header>
      <v-stepper-step :complete="stepper > 1" step="1">
        Sites
        <small class="d-none d-xl-flex">Selection location A to B</small>
      </v-stepper-step>

      <v-divider></v-divider>

      <v-stepper-step :complete="stepper > 2" step="2">
        Fleet
        <small class="d-none d-xl-flex">Selection of ships within a fleet</small>
      </v-stepper-step>

      <v-divider></v-divider>

      <v-stepper-step :complete="stepper > 3" step="3">
        Climate
        <small class="d-none d-xl-flex">Set climate conditions</small>
      </v-stepper-step>

      <v-divider></v-divider>

      <v-stepper-step :complete="stepper > 4" step="4">
        Load
        <small class="d-none d-xl-flex">Cargo loading</small>
      </v-stepper-step>

      <v-divider></v-divider>

      <v-stepper-step :complete="stepper > 5" step="5">
        Animation
        <small class="d-none d-xl-flex">Visualisation of traffic</small>
      </v-stepper-step>

      <v-stepper-step :complete="stepper > 5" step="6">
        KPI
        <small class="d-none d-xl-flex">Key peformance indicators</small>
      </v-stepper-step>
    </v-stepper-header>

    <v-stepper-items class="stepper-content">
      <v-stepper-content step="1">
        <h2 class="text-h4 mb-5">Sites</h2>
        <v-divider class="mb-6" />
        <sites-component ref="sites" :map="map" />
      </v-stepper-content>

      <v-stepper-content step="2">
        <h2 class="text-h4 mb-5">Fleet selection</h2>
        <v-divider class="mb-6" />
        <fleet-component ref="fleet" />
      </v-stepper-content>

      <v-stepper-content step="3">
        <h2 class="text-h4 mb-5">Climate</h2>
        <v-divider class="mb-6" />
        <climate-component ref="climate" />
      </v-stepper-content>

      <v-stepper-content step="4">
        <h2 class="text-h4 mb-5">Load</h2>
        <v-divider class="mb-6" />
        <load-component ref="load" />
      </v-stepper-content>

      <v-stepper-content step="5">
        <h2 class="text-h4 mb-5">Animation</h2>
        <v-divider class="mb-2" />
        <result-component :config="config" />
      </v-stepper-content>

      <v-stepper-content step="6">
        <h2 class="text-h4 mb-5">KPI</h2>
        <v-divider class="mb-2" />
        <kpi-component />
      </v-stepper-content>
    </v-stepper-items>
    <div class="pa-4 mt-auto d-flex stepper-footer">
      <v-btn v-if="stepper > 1" text @click="prevStep">Back</v-btn>

      <v-btn
        v-if="stepper < maxStep "
        :disabled="!stepOk(stepper)"
        color="primary"
        class="ml-auto"
        @click="nextStep"
      >Continue</v-btn>
    </div>
  </v-stepper>
</template>

<script>
import FleetComponent from './FleetComponent'
import SitesComponent from './SitesComponent'
import ClimateComponent from './ClimateComponent'
import LoadComponent from './LoadComponent'
import ResultComponent from './ResultComponent'
import KpiComponent from './KpiComponent'
import { mapState, mapActions, mapGetters } from 'vuex'

export default {
  props: {
    map: Object
  },
  data() {
    return {
      stepper: 1,
      maxStep: 6
    }
  },
  components: {
    FleetComponent,
    SitesComponent,
    ClimateComponent,
    ResultComponent,
    LoadComponent,
    KpiComponent
  },
  computed: {
    ...mapState(['route', 'waypoints']),
    ...mapGetters(['config', 'fleet', 'climate'])
  },
  watch: {
    stepper(value) {
      if (value === 5) {
        this.startSailing()
      }
    }
  },
  methods: {
    ...mapActions(['fetchResults']),
    stepOk(step) {
      if (step === 1) {
        // make sure we have sites selected before we procede
        if (!(this.config?.sites?.length >= 2)) {
          return false
        }
      } else if (step === 2) {
        if (!(this.config?.fleet?.length >= 1)) {
          return false
        }
      }
      return true
    },
    startSailing() {
      this.fetchResults(this.config)
    },
    nextStep() {
      if (this.stepper < this.maxStep) {
        this.stepper = this.stepper + 1
      }
    },
    prevStep() {
      if (this.stepper > 1) {
        this.stepper = this.stepper - 1
      }
    }
  }
}
</script>

<style>
.stepper {
  max-height: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.v-stepper__header {
  box-shadow: none !important;
  border-bottom: thin solid rgba(0, 0, 0, 0.12);
}

.v-stepper__content {
  max-height: 100%;
  overflow-y: auto;
}

.stepper-footer {
  border-top: thin solid rgba(0, 0, 0, 0.12);
}
</style>
