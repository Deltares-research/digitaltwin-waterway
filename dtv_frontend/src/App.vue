<template>
  <v-app>
    <v-app-bar class="app-header" app >
      <v-toolbar-title> Digital Twin - waterways </v-toolbar-title>
    </v-app-bar>
    <v-main>
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'App',
  components: {
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
