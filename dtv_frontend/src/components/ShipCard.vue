<template>
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
      <v-slider
        :min="0"
        :max="20"
        label="# ships"
        thumb-label="always"
        v-model="ship.count"
        @change="updateShip(ship)"
      ></v-slider>
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
              <td>
                <v-text-field
                  v-model="ship[item]"
                  :disabled="!editable.includes(item)"
                  @change="updateShip(ship)"
                ></v-text-field>
              </td>
            </tr>
            <tr>
              <td>Energy carrier</td>
              <td>
                <v-select
                  :items="energyCarriers"
                  v-model="energyCarrier"
                  disabled
                  @change="updateShip(ship)"
                ></v-select>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
      <v-sheet
        color="grey darken-2 mt-3"
        elevation="5"
        v-show="ship['RWS-class'] === 'M12'"
        class="small-chart"
      >
        <v-chart :option="m12" :init-options="initOptions" />
      </v-sheet>
    </v-card-text>
  </v-card>
</template>
<script>
import { mapState } from 'vuex'
import { THEME_KEY } from 'vue-echarts'
export default {
  props: {
    ship: Object
  },
  provide: {
    [THEME_KEY]: 'dark'
  },
  data() {
    return {
      initOptions: {
        renderer: 'svg',
        width: 340
      },
      editable: [
        'name',
        'Length [m]',
        'Beam [m]',
        'Engine power maximum [kW]',
        'Velocity [m/s]'
      ],
      // hard coded (not available yet)
      energyCarrier: 'Diesel',
      energyCarriers: ['Diesel', 'LPG', 'LNG', 'H2'],
      tableProperties: [
        'name',
        'Vessel type',
        'CEMT-class',
        'RWS-class',
        'Length [m]',
        'Beam [m]',
        'Load weight maximum [ton]',
        'Velocity [m/s]',
        'Engine power maximum [kW]'
      ]
    }
  },
  computed: {
    ...mapState(['m12'])
  },
  methods: {
    updateShip(ship) {
      this.$emit('change', ship)
    }
  }
}
</script>
<style>
.small-chart {
  height: 400px;
  width: 100%;
}
</style>
