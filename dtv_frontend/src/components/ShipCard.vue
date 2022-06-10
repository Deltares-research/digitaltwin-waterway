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
              <td>
                <v-text-field v-model="ship[item]" :disabled="!editable.includes(item)"></v-text-field>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
    </v-card-text>
  </v-card>
</template>
<script>
export default {
  props: {
    ship: Object
  },
  data() {
    return {
      editable: ['name', 'Length [m]', 'Beam [m]'],
      tableProperties: [
        'name',
        'Vessel type',
        'CEMT-class',
        'RWS-class',
        'Length [m]',
        'Beam [m]'
      ]
    }
  }
}
</script>
