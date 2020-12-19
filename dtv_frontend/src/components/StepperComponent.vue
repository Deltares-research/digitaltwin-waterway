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
      <sites-component class="mb-3" ref="sites"></sites-component>
      <v-btn
        color="primary"
        @click="stepper = 2"
      >
        Continue
      </v-btn>
      <v-btn
        text
        @click="stepper = 1"
      >
        Back
      </v-btn>
    </v-stepper-content>

    <v-stepper-step
      :complete="stepper > 2"
      step="2"
      @click="stepper = 2"
    >
      Fleet
      <small>Selection of ships within a fleet</small>
    </v-stepper-step>

    <v-stepper-content step="2" class="stepper-fleet">
      <fleet-component class="mb-3 d-flex-grow fleets" ref="fleet"/>
      <v-row>
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
        </v-row>
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
      <climate-component class="mb-3"/>
      <v-btn
        color="primary"
        @click="startSailing"
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
  methods: {
    ...mapActions(['fetchResults']),
    startSailing () {
      this.stepper = 4
      this.fetchResults(this.config)
    }
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

  }
}
</script>

<style>
.stepper {
  max-height: 100%;
  height: 100%;
}

.stepper-fleet {
  max-height: 60vh;
}
</style>
