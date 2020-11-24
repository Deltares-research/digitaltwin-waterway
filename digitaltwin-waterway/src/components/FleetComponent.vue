<template>
<v-container>
  <h2> Fleet selection</h2>
  <v-row dense>
    <v-col
      cols="12"
      sm="6" md="4" xs="12"
      v-for="(ship, index) in ships" :key="index">

      <v-card
        class="ma-3"
        outlined
        hover
        >
        <v-card-title>
          <v-checkbox></v-checkbox> {{ ship['Description (Dutch)'] }}
        </v-card-title>
        <!-- TODO: add color, icon/image -->
        <v-card-text>
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
      console.log('ships', ships)
      return ships
    }
  }

}
</script>
