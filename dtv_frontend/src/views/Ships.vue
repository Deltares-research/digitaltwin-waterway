<template>
<v-container>
  <v-row>
    <v-card class="ma-2 pa-2 form-card">
      <v-select
        :items="shipTypes"
        label="Ship type"
        v-model="shipType"
        ></v-select>
      <v-slider :label="label" thumb-label v-model="cargo" min="0" :max="maxCargo" :step="stepCargo"></v-slider>
    </v-card>
    <v-card class="ma-2 pa-0 ship-card" >
      <svg viewBox="0 0 720 144" class="ship">
        <rect class="background" x="0" y="0" width="720" height="144"></rect>
        <use :href="shipSvg" class="blueprint" :y="shipY" x="36"></use>
        <line class="water" x1="0" y1="110" x2="720" y2="110"></line>
        <rect class="water-mask" x="0" y="110" width="720" height="34"></rect>
      </svg> <!--  -->
    </v-card>
    <v-card class="ma-2 bridges-card"> bridges</v-card>

  </v-row>
</v-container>
</template>
<script>
import { mapActions } from 'vuex'

const TONNE_PER_TEU = 20

export default {
  name: 'Ships',
  data () {
    return {
      cargo: 10,
      shipTypes: ['Bulk', 'Container'],
      shipType: null
    }
  },
  computed: {
    shipY () {
      const maxY = 25
      const fractionLoaded = this.cargo / this.maxCargo
      return maxY * fractionLoaded
    },
    shipSvg () {
      if (this.shipType === 'Bulk') {
        return 'graphics/container-ship_Bulk-short.svg#Bulk-short'
      } else {
        return 'graphics/container-ship_Container-short.svg#Container-short'
      }
    },
    unit () {
      if (this.shipType === 'Bulk') {
        return 'Tonne'
      } else {
        return 'TEU'
      }
    },
    maxCargo () {
      // Compute max cargo in Tonne
      if (this.shipType === 'Bulk') {
        return 2500
      } else {
        return 400 * TONNE_PER_TEU
      }
    },
    stepCargo () {
      // Cargo step in Tonne
      if (this.shipType === 'Bulk') {
        return 100
      } else {
        return 10 * TONNE_PER_TEU
      }
    },
    label () {
      return `Cargo [${this.unit}]`
    }
  },
  components: {
  },
  created () {
  },
  methods: {
    ...mapActions(['fetchSites'])
  }
}
</script>

<style lang="scss">
@import '~vuetify/src/styles/main.sass';

$blueprint: map-get($blue, 'darken-4');
$blueprint-light: map-get($blue, 'lighten-5');

.form-card {
  width: 100vw;
}
.ship-card {
  width: 100vw;
  line-height: 0;
}
.bridges-card {
  width: 100vw;
}

.background {
  fill: $blueprint;
}

.blueprint {
  fill: none;
  stroke: $blueprint-light;
  stroke-width: 0.2px;
}
.water {
  stroke: $blueprint-light;
  stroke-width: 0.5px;
}
.water-mask  {
  fill: rgba($blueprint, 0.5);
}
</style>
