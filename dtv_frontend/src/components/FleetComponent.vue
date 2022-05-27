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
        <v-card outlined>
          <v-card-title>
            {{ ship['Description (Dutch)'] }}
            <v-spacer />
            <v-avatar size="50px">
              <v-icon>mdi-ferry</v-icon>
            </v-avatar>
          </v-card-title>
          <!-- TODO: add color, icon/image -->
          <v-card-text>
            <v-slider :min="0" :max="20" label="# ships" thumb-label="always" v-model="ship.count"></v-slider>
            <v-simple-table dense>
              <template v-slot:default>
                <thead>
                  <tr>
                    <th class="text-left">Property</th>
                    <th class="text-left">Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in tableProperties" :key="item">
                    <td>{{ item }}</td>
                    <td>{{ ship[item] }}</td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import _ from 'lodash'

export default {
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
      ],
      tableProperties: [
        'Vessel type',
        'CEMT-class',
        'RWS-class',
        'Length [m]',
        'Beam [m]'
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
    }
  },
  methods: {
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
