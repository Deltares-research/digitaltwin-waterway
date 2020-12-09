<template>
<v-container>
  <h2> Fleet selection</h2>

  <v-row dense>
    <v-col
      cols="12"
      sm="6" xs="12"
      v-for="(ship, index) in ships" :key="index">

      <v-card
        class="ma-3"
        outlined
        hover
        >
        <v-card-title>
          {{ ship['Description (Dutch)'] }}
          <v-spacer />
          <v-avatar size="50px">
            <img :src="ship.image">
          </v-avatar>
        </v-card-title>
        <!-- TODO: add color, icon/image -->
        <v-card-text>
          <v-slider
            :min="0"
            :max="20"
            label="# ships"
            thumb-label
            v-model="ship.count"
          ></v-slider>
          <v-simple-table dense>
            <template v-slot:default>
              <thead>
                <tr>
                  <th class="text-left">
                    Property
                  </th>
                  <th class="text-left">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in tableProperties"
                  :key="item"
                >
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
</v-container>
</template>

<script>
export default {
  data () {
    return {
      ships: [],
      tableProperties: [
        'Vessel type',
        'CEMT-class',
        'RWS-class',
        'Length [m]',
        'Beam [m]'
      ]
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
      /* add ship count  */
      ships.forEach((ship) => {
        ship.count = 0
      })
      return ships
    }
  }

}
</script>
