<template>
  <v-stepper class="stepper" v-model="stepper">
    <v-stepper-header>
      <v-stepper-step
        :complete="stepper > 1"
        step="1"
      >
        Sites
        <small class="d-none d-xl-flex">Selection location A to B</small>
      </v-stepper-step>

      <v-divider></v-divider>

      <v-stepper-step
        :complete="stepper > 2"
        step="2"
      >
        Fleet
        <small class="d-none d-xl-flex">Selection of ships within a fleet</small>
      </v-stepper-step>

      <v-divider></v-divider>

      <v-stepper-step
        :complete="stepper > 3"
        step="3"
      >
        Climate
        <small class="d-none d-xl-flex">Set climate conditions</small>
      </v-stepper-step>

      <v-divider></v-divider>

      <v-stepper-step
        :complete="stepper > 3"
        step="4"
      >
        Results
        <small class="d-none d-xl-flex">charts and visualisations</small>
      </v-stepper-step>
    </v-stepper-header>

    <v-stepper-items class="stepper-content">
      <v-stepper-content step="1">
        <h2 class="text-h4 mb-5">Sites</h2>
        <v-divider class="mb-6" />
        <sites-component ref="sites" />
      </v-stepper-content>

      <v-stepper-content step="2">
        <h2 class="text-h4 mb-5 ">Fleet selection</h2>
        <v-divider class="mb-6" />
        <fleet-component ref="fleet" />
      </v-stepper-content>

      <v-stepper-content step="3">
        <h2 class="text-h4 mb-5 ">Climate</h2>
        <v-divider class="mb-6" />
        <climate-component />
      </v-stepper-content>

      <v-stepper-content step="4">
        <h2 class="text-h4 mb-5">Results</h2>
        <v-divider class="mb-2" />
        <result-component />
      </v-stepper-content>
    </v-stepper-items>
    <div class="pa-4 mt-auto d-flex stepper-footer">
      <v-btn
        v-if="stepper > 1"
        text
        @click="prevStep"
      >
        Back
      </v-btn>

      <v-btn
        v-if="stepper < 4"
        color="primary"
        class="ml-auto"
        @click="nextStep"
      >
        Continue
      </v-btn>
    </div>
  </v-stepper>
</template>

<script>
import FleetComponent from './FleetComponent'
import SitesComponent from './SitesComponent'
import ClimateComponent from './ClimateComponent'
import ResultComponent from './ResultComponent'
import { mapState, mapActions } from 'vuex'

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
  computed: {
    ...mapState(['sites']),
    config () {
      return {
        sites: this.sites.features,
        fleet: this.fleet,
        operator: { name: 'Operator' }
      }
    },
    fleet () {
      const fleet = []
      this.$refs.fleet.ships.forEach(ship => {
        for (var i = 0; i < ship.count; i++) {
          fleet.push(ship)
        }
      })
      const features = fleet.map((ship, i) => {
        const geometry = this.sites.features[0].geometry
        const feature = {
          type: 'Feature',
          id: i,
          geometry: geometry,
          properties: ship
        }
        return feature
      })
      return features
    }
  },
  watch: {
    stepper (value) {
      if (value === 4) {
        this.startSailing()
      }
    }
  },
  methods: {
    ...mapActions(['fetchResults']),
    startSailing () {
      this.fetchResults(this.config)
    },
    nextStep () {
      if (this.stepper < 4) {
        this.stepper = this.stepper + 1
      }
    },
    prevStep () {
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
  border-bottom: thin solid rgba(0,0,0,.12);
}

.v-stepper__content {
  max-height: 100%;
  overflow-y: auto;
}

.stepper-footer {
  border-top: thin solid rgba(0,0,0,.12);
}
</style>
