<template>
<div>
  <h2> Fleet selection</h2>
  <v-card
    class="ma-3"
    outlined
    v-for="(ship, index) in ships" :key="index">
    <v-card-title>
      <v-checkbox
        v-model="checkbox"
      ></v-checkbox> {{ ship['Description (Dutch)'] }}
    </v-card-title>
    <!-- TODO: add color, icon/image -->
    <v-card-text>
      <v-simple-table>
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
</div>
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
