<template>
  <v-app>
    <v-app-bar class="app-header" app color="primary" dark>
      <v-toolbar-title> Digital Twin - waterways </v-toolbar-title>
    </v-app-bar>
    <v-main>
      <v-row class="main-row" no-gutters>
        <v-col class="pa-3 main-row" cols="12" md="6">
          <stepper-component />
        </v-col>
        <v-col class="pa-0" cols="12" md="6">
          <map-component />
        </v-col>
      </v-row>
    </v-main>
  </v-app>
</template>

<script>
import MapComponent from './components/MapComponent'
import StepperComponent from './components/StepperComponent'
import { mapActions } from 'vuex'

export default {
  name: 'App',
  components: {
    MapComponent,
    StepperComponent
  },
  created () {
    this.fetchResults()
    this.fetchSites()
  },
  methods: {
    ...mapActions(['fetchResults', 'fetchSites'])
  }
}
</script>

<style>

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.v-main {
  height: 100vh;
}

.main-row {
  height: 100%;
}

</style>
