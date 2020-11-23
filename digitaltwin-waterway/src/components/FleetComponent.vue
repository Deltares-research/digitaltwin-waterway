<template>
  <v-card class="py-3">
    <h2> Fleet </h2>
    <v-card
      class="ma-3"
      outlined
      v-for="(ship, index) in ships" :key="index">
      <v-card-title>
        {{ ship.title }}
      </v-card-title>
      <v-card-subtitle>
        {{ ship.subtitle }}
      </v-card-subtitle>
      <v-progress-linear
        :color="ship.color"
        :value="ship.progress"
        height="25"
        stream
      ></v-progress-linear>
    </v-card>
  </v-card>
</template>

<script>
export default {
  data () {
    return {
      ships: [{
        title: 'Ship A',
        subtitle: 'Nice vessel',
        color: 'blue',
        progress: 40
      }]
    }
  }
}
</script>
