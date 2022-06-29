<template>
  <div>
    <v-row dense>
      <v-card>
        <v-card-title>
          Ships
          <v-spacer></v-spacer>
          <v-text-field
            v-model="search"
            append-icon="mdi-magnify"
            label="Search"
            single-line
            hide-details
          ></v-text-field>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="ships"
            :items-per-page="10"
            class="elevation-1"
            item-key="name"
            :search="search"
            v-model="selectedShips"
            show-select
          ></v-data-table>
        </v-card-text>
      </v-card>
    </v-row>
    <v-row dense>
      <v-col cols="12" sm="6" xs="12" v-for="(ship, index) in selectedShips" :key="index">
        <ship-card :ship="ship" @change="updateFleet"></ship-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import ShipCard from './ShipCard'
import _ from 'lodash'

import { mapMutations } from 'vuex'

export default {
  components: {
    ShipCard
  },
  data() {
    return {
      ships: [],
      selectedShips: [],
      search: '',
      headers: [
        {
          text: 'Description (English)',
          value: 'Description (English)'
        },
        {
          text: 'Vessel type',
          value: 'Vessel type'
        },
        {
          text: 'CEMT-class',
          value: 'CEMT-class'
        },
        {
          text: 'RWS-class',
          value: 'RWS-class'
        },
        {
          text: 'Length [m]',
          value: 'Length [m]'
        },
        {
          text: 'Beam [m]',
          value: 'Beam [m]'
        }
      ]
    }
  },
  mounted() {
    this.fetchShips().then((ships) => {
      this.ships = ships
    })
  },
  watch: {
    selectedShips(ships) {
      // if a ship is added, update count to default to 1
      // update counts
      const notSelectedShips = _.difference(this.ships, ships)
      // reset not selected ship count to 0
      notSelectedShips.forEach((ship) => {
        ship.count = 0
      })
      // set selected ship count to 1 if set to 0
      ships.forEach((ship) => {
        if (ship.count === 0) {
          ship.count = 1
        }
      })
      this.setFleet(ships)
    }
  },
  methods: {
    ...mapMutations(['setFleet']),
    updateFleet() {
      this.setFleet(this.selectedShips)
    },
    async fetchShips() {
      const resp = await fetch('data/DTV_shiptypes_database.json')
      const ships = await resp.json()
      /* add ship count  */
      ships.forEach((ship) => {
        ship.capacity = ship['Load Weight average [ton]']
        ship.name = ship['Description (English)']
        ship.count = 0
      })
      return ships
    }
  }
}
</script>
