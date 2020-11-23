<template>
  <v-card class="py-3">
    <h2> Fleet </h2>
    <v-card
      class="ma-3"
      outlined
      v-for="(ship, index) in ships" :key="index">
      <v-card-title>
        {{ ship['Description (Dutch)'] }}
      </v-card-title>
      <!-- TODO: add color, icon/image -->
      <v-card-subtitle>
        Vessel type: {{ ship['Vessel type'] }}, CEMT: {{ ship['CEMT-class'] }}, RWS: {{ ship['RWS-class'] }}
        Length: {{ ship['Length [m]'] }}m, Beam: {{ ship['Beam [m]']}}m
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
      ships: []
    }
  },
  mounted () {
    this.fetchShips().then((ships) => {
      this.ships = ships
    })
  },
  methods: {
    async fetchShips () {
      const resp = await fetch('data/DTV_shiptypes_database.json')
      const ships = await resp.json()
      console.log('ships', ships)
      return ships
    }
  }

}
</script>
