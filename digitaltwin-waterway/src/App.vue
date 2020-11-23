<template>
  <v-app>
    <v-app-bar class="app-header" app color="primary" dark>
      <v-toolbar-title> Digital Twin - waterways </v-toolbar-title>
    </v-app-bar>
    <v-main>
      <v-row class="main-row" no-gutters>
        <v-col class="pa-3" cols="12" md="4">
          <sites-component />
        </v-col>
        <v-col class="pa-3" cols="12" md="4">
          <fleet-component />
        </v-col>
        <v-col class="pa-0" cols="12" md="4">
          <map-component />
        </v-col>
      </v-row>
    </v-main>
  </v-app>
</template>

<script>
import MapComponent from './components/MapComponent'
import FleetComponent from './components/FleetComponent'
import SitesComponent from './components/SitesComponent'

export default {
  name: 'App',
  components: {
    MapComponent,
    FleetComponent,
    SitesComponent
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

.main-row {
  height: 100%;
}

</style>
