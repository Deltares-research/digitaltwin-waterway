<template>
  <div>
    <v-card>
      <v-card-text class="pa-2">
        <h2>Clearance</h2>
        <p>Set the underkeel clearance and vertical clearance safety margins.</p>
        <v-slider
          :step="0.5"
          inverse-label
          :min="0"
          :max="30"
          label="Under keel clearance [cm]"
          thumb-label="always"
          v-model="underKeelClearance"
          ></v-slider>
        <v-slider
          :step="0.5"
          inverse-label
          :min="0"
          :max="30"
          label="Vertical clearance [cm]"
          thumb-label="always"
          v-model="verticalClearance"
          ></v-slider>
      </v-card-text>
    </v-card>

    <v-card class="mt-2 form-card">
      <v-card-text class="pa-2">
        <h2>Ship type</h2>
        <p>Select which ship you want to load</p>
        <v-select
        :items="shipTypes"
        label="Ship type"
        v-model="shipType"
        ></v-select>
        <v-slider
          :label="label"
          inverse-label
          min="0"
          v-model="cargo"
          :max="maxCargo"
          :step="stepCargo"
          thumb-label="always"
          ></v-slider>
      </v-card-text>
    </v-card>

    <v-card class="mt-2 ship-card" >
      <v-card-text class="pa-2">
        <h2>Draught / clearance</h2>
      </v-card-text>
      <svg viewBox="0 -100 720 344" class="ship">
        <defs>
          <marker id="arrowend" viewBox="0 0 13 10" refX="8" refY="5" markerWidth="3.5" markerHeight="3.5" orient="auto">
            <path d="M 0 0  C 0 0, 3 5, 0 10   L 0 10  L 13 5" class="arrowhead" />
          </marker>

          <marker id="arrowstart" viewBox="0 0 13 10" refX="5" refY="5" markerWidth="3.5" markerHeight="3.5" orient="auto">
            <path d="M 13 0  C 13 0, 10 5, 13 10   L 13 10  L 0 5" class="arrowhead"/>
          </marker>
        </defs>
        <rect class="background" x="0" y="-100" width="720" height="344"></rect>
        <use :href="shipSvg" class="blueprint" :y="shipY" x="36"></use>
        <line class="water" x1="0" y1="110" x2="720" y2="110"></line>
        <line class="ground" x1="0" y1="144" x2="720" y2="144"></line>
        <rect class="ground" x="0" y="144" width="720" height="10"></rect>
        <rect class="bridge" x="690" y="0" width="40" height="10"></rect>
        <rect class="bridge-pilar" x="710" y="10" width="5" height="150"></rect>
        <line class="arrow" x1="120" :y1="110 + 1" x2="120" :y2="110 + shipY - 1"></line>
        <line class="arrow" x1="100" :y1="110 + shipY + 1" x2="100" :y2="144 - 1"></line>
        <rect class="water-mask" x="0" y="110" width="720" height="34"></rect>
        <text x="125" :y="110 + shipY / 2">T</text>
        <text x="105" :y="110 + 17 + shipY / 2">UKC</text>
      </svg> <!--  -->
    </v-card>
    <v-card class="mt-2 bridges-card">
      <v-card-text>
        <h2>Route profile</h2>
      </v-card-text>

      <v-img alt="" src="graphics/profile-emo-bctn.png"/>
    </v-card>

  </div>

</template>
<script>
const TONNE_PER_TEU = 20

export default {
  name: 'LoadComponent',
  components: {
  },
  data () {
    return {
      cargo: 10,
      shipTypes: ['Bulk', 'Container'],
      shipType: 'Bulk',
      underKeelClearance: 20,
      verticalClearance: 20
    }
  },
  computed: {
    shipY () {
      const maxY = 15
      const minY = 10
      const fractionLoaded = this.cargo / this.maxCargo
      return minY + maxY * fractionLoaded
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
        return 400
      }
    },
    stepCargo () {
      // Cargo step in Tonne
      if (this.shipType === 'Bulk') {
        return 100
      } else {
        return 10
      }
    },
    label () {
      return `Cargo [${this.unit}]`
    }
  },
  watch: {
    shipType (newValue, oldValue) {
      if (newValue === 'Bulk' & oldValue === 'Container') {
        this.cargo *= TONNE_PER_TEU
      } else if (newValue === 'Container' & oldValue === 'Bulk') {
        this.cargo /= TONNE_PER_TEU
      }
    }
  }
}
</script>
<style lang="scss" scoped>
  @import '~vuetify/src/styles/main.sass';

  $blueprint: map-get($blue, 'darken-4');
  $blueprint-light: map-get($blue, 'lighten-5');
  $blueprint-brown: adjust-hue(map-get($blue, 'lighten-3'), 180deg);

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

.water-mask  {
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

@keyframes dash {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: 10;
  }
}
</style>
