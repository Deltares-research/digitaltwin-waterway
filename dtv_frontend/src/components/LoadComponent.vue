<template>
<div>
  <h2 class="mb-2">Safety margins</h2>
  <v-card>
    <v-card-title class="pa-2">
      Clearance
    </v-card-title>
    <v-card-text class="pa-2">
      <p>Set the safety margins for underkeel clearance and vertical clearance.</p>
      <v-slider
        :step="0.01"
        inverse-label
        :min="0"
        :max="0.3"
        label="Under keel clearance [m]"
        thumb-label="always"
        v-model="underKeelClearanceMargin"
        ></V-slider>
      <v-slider
        :step="0.01"
        inverse-label
        :min="0"
        :max="0.3"
        label="Vertical clearance [m]"
        thumb-label="always"
        v-model="verticalClearanceMargin"
        ></v-slider>
    </v-card-text>
  </v-card>
  <div v-for="ship in fleet" :key="ship['RWS-class']">
    <v-divider class="mt-2 mb-2"></v-divider>
    <h2>Ship type: {{ship['RWS-class']}}</h2>

    <v-card class="mt-2 form-card">
      <v-card-title class="pa-2">Cargo</v-card-title>
      <v-card-text class="pa-2">
        <v-slider
          label="Cargo [ton]"
          inverse-label
          min="0"
          v-model="ship.capacity"
          :max="ship['Load weight maximum [ton]']"
          :step="stepCargo"
          thumb-label="always"
          ></v-slider>
      </v-card-text>
    </v-card>

    <v-card class="mt-2 ship-card">
      <v-card-title class="pa-2">Draught / clearance</v-card-title>

      <svg viewBox="0 -100 720 344" class="ship">
        <!-- 1px =? 0.1m -->
        <defs>
          <marker
            id="arrowend"
            viewBox="0 0 13 10"
            refX="8"
            refY="5"
            markerWidth="3.5"
            markerHeight="3.5"
            orient="auto"
            >
            <path d="M 0 0  C 0 0, 3 5, 0 10   L 0 10  L 13 5" class="arrowhead" />
          </marker>

          <marker
            id="arrowstart"
            viewBox="0 0 13 10"
            refX="5"
            refY="5"
            markerWidth="3.5"
            markerHeight="3.5"
            orient="auto"
            >
            <path d="M 13 0  C 13 0, 10 5, 13 10   L 13 10  L 0 5" class="arrowhead" />
          </marker>
        </defs>
        <rect class="background" x="0" y="-100" width="720" height="344" />
        <use :href="shipSvg" class="blueprint" :y="shipY(ship)" x="36" />
        <line class="water" x1="0" y1="110" x2="720" y2="110" />
        <line class="ground" x1="0" y1="144" x2="720" y2="144" />
        <rect class="ground" x="0" y="144" width="720" height="10" />
        <rect class="bridge" x="690" y="0" width="40" height="10" />
        <rect class="bridge-pilar" x="710" y="10" width="5" height="150" />
        <line class="arrow" x1="120" :y1="110 + 1" x2="120" :y2="110 + shipY(ship) - 1" />
        <line class="arrow" x1="100" :y1="110 + shipY(ship) + 1" x2="100" :y2="144 - 1" />
        <line class="alert" x1="0" :y1="144 - underKeelClearanceMargin * 0.1" x2="720" :y2="144 - underKeelClearanceMargin * 0.1" />
        <line class="alert" x1="0" :y1="10 + verticalClearanceMargin * 0.1" x2="720" :y2="10 + verticalClearanceMargin * 0.1" />
        <rect class="water-mask" x="0" y="110" width="720" height="34" />
        <text x="125" :y="110 + shipY(ship) / 2">T</text>
        <text x="105" :y="110 + 17 + shipY(ship) / 2">UKC</text>
        <text x="0" :y="144 - underKeelClearanceMargin * 0.1 - 5">UKC safety margin</text>
        <text x="0" :y="10 + verticalClearanceMargin * 0.1 - 5">Vertical Clearance safety margin</text>
      </svg>
      <v-card-text>
        <v-simple-table>
          <template v-slot:default>
            <tbody>
              <tr>
                <td>Underkeel margin [m]:</td>
                <td class="text-right" >
                  <v-alert
                    :type="(ukc(ship) - underKeelClearanceMargin) > 0 ? 'success' : 'warning' "
                    >
                    {{ (ukc(ship) - underKeelClearanceMargin).toFixed(2) }}
                  </v-alert>
                </td>
              </tr>
              <tr>
                <td>Draught empty [m]:</td>
                <td class="text-right">{{ ship['Draught empty [m]'] }}</td>
              </tr>
              <tr>
                <td>Draught loaded [m]:</td>
                <td class="text-right">{{ ship['Draught loaded [m]'] }}</td>
              </tr>
              <tr>
                <td>Draught [m]:</td>
                <td class="text-right">{{ draught(ship).toFixed(2) }}</td>
              </tr>
              <tr>
                <td>Minimum depth on route [m]:</td>
                <td class="text-right">{{ minDepthOnRoute }}</td>
              </tr>
              <tr>
                <td>Underkeel clearance [m]:</td>
                <td class="text-right">{{ ukc(ship).toFixed(2) }}</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-card-text>

      <!--  -->
    </v-card>

  </div>
  <v-card class="mt-2 bridges-card" v-if="routeProfile">
    <v-card-title>Route Profile</v-card-title>
    <v-img alt="route profile" :src="routeProfileSrc"  />
  </v-card>
</div>
</template>
<script>
import { mapGetters } from 'vuex'
import { mapFields } from 'vuex-map-fields'
import _ from 'lodash'

export default {
  name: 'LoadComponent',
  components: {},
  data() {
    return {
      cargoPerShipType: {},
      underKeelClearanceMargin: 20,
      verticalClearanceMargin: 20
    }
  },
  computed: {
    ...mapGetters(['unit']),
    ...mapFields(['cargoType', 'fleet', 'prototypeShips', 'routeProfile']),
    shipTypes() {
      const types = _.uniq(_.map(this.fleet, 'properties.RWS-class'))
      types.sort()
      return types
    },
    shipSvg() {
      if (this.shipType === 'Bulk') {
        return 'graphics/container-ship_Bulk-short.svg#Bulk-short'
      } else {
        return 'graphics/container-ship_Container-short.svg#Container-short'
      }
    },
    maxCargo() {
      // Compute max cargo in Tonne
      if (this.cargoType === 'Dry Bulk') {
        return 2500
      } else {
        return 400
      }
    },
    stepCargo() {
      // Cargo step in Tonne
      if (this.cargoType === 'Dry Bulk') {
        return 100
      } else {
        return 10
      }
    },
    label() {
      return `Cargo [${this.unit}]`
    },
    minDepthOnRoute() {
      return 3
    },
    routeProfileSrc() {
      return URL.createObjectURL(this.routeProfile)
    }

  },
  methods: {
    shipY(ship) {
      const maxY = 15
      const minY = 10
      return minY + maxY * this.loadedFraction(ship)
    },
    loadedFraction(ship) {
      return ship.capacity / ship['Load weight maximum [ton]']
    },
    ukc(ship) {
      return this.minDepthOnRoute - this.draught(ship)
    },
    draught(ship) {
      const draughtRange = (ship['Draught loaded [m]'] - ship['Draught empty [m]'])
      const minDraught = ship['Draught empty [m]']
      return minDraught + (draughtRange * this.loadedFraction(ship))
    }
  }
}
</script>
<style lang="scss" scoped>
@import '~vuetify/src/styles/main.sass';

$blueprint: map-get($blue, 'darken-4');
$blueprint-light: map-get($blue, 'lighten-5');
$blueprint-brown: adjust-hue(map-get($blue, 'lighten-3'), 180deg);
$blueprint-orange: adjust-hue(map-get($blue, 'lighten-3'), 120deg);

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

.ship text {
    fill: $blueprint-light;
    font-size: xx-small;
    text-anchor: start;
    alignment-baseline: middle;
}
.blueprint {
    fill: none;
    stroke: $blueprint-light;
    stroke-width: 0.2px;
}
.water {
    stroke: $blueprint-light;
    stroke-width: 0.5px;
    stroke-dasharray: 3 7;
    animation: dash 2s linear infinite;
}
.bridge {
    stroke: $blueprint-light;
    stroke-width: 0.5px;
    fill: none;
}
.bridge-pilar {
    stroke: $blueprint-light;
    stroke-width: 0.5px;
    stroke-dasharray: 1 4;
    fill: none;
}

line.ground {
    stroke: $blueprint-brown;
    stroke-width: 0.5px;
}
rect.ground {
    fill: $blueprint-brown;
    opacity: 0.1;
}

.water-mask {
    fill: rgba($blueprint, 0.5);
}
.arrow {
    stroke: $blueprint-light;
    stroke-width: 2px;
    marker-end: url(#arrowend);
    marker-start: url(#arrowstart);
    vector-effect: non-scaling-stroke;
}
.arrowhead {
    stroke: $blueprint-light;
    stroke-width: 1;
    fill: $blueprint-light;
}

line.alert {
    stroke: $blueprint-orange;
    stroke-width: 0.5;
    fill: none;
}

@keyframes dash {
    0% {
        stroke-dashoffset: 0;
    }
    100% {
        stroke-dashoffset: 10;
    }
}
</style>
