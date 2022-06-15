<template>
  <div>
    <v-tabs>
      <v-tab key="discharge">Discharge</v-tab>
      <v-tab key="sl">Sea level</v-tab>

      <v-tab-item key="discharge" class="climate-scenario">
        <v-card outlined>
          <v-card-text>
            <h2>Rhine discharge</h2>
            <p>In/decrease the discharge at Lobith. This influences water depths and currents over the whole river.</p>
            <v-slider
              :step="1000"
              inverse-label
              :min="1000"
              :max="12000"
              label="Rhine discharge [m3/s]"
              thumb-label="always"
              @change="updateClimate"
              v-model="lobithDischarge"
            ></v-slider>
            <v-slider
              inverse-label
              :min="0"
              :max="600"
              disabled
              label="Nijmegen waterlevel"
              thumb-label="always"
              v-model="nijmegen"
            ></v-slider>
            <v-slider
              inverse-label
              :min="0"
              :max="600"
              disabled
              label="Kaub waterlevel"
              thumb-label="always"
              v-model="kaub"
            ></v-slider>
            <v-slider
              inverse-label
              :min="0"
              :max="600"
              disabled
              label="Duisburg waterlevel"
              thumb-label="always"
              v-model="duisburg"
            ></v-slider>
          </v-card-text>
        </v-card>

        <v-card outlined>
          <v-card-text>
            <h2>Maas discharge</h2>
            <p>In/decrease the discharge at st Pieter. This influences water depths and currents over the whole Maas river.</p>
            <v-slider
              :step="100"
              inverse-label
              :min="100"
              :max="4000"
              label="st Pieter discharge [m3/s]"
              thumb-label="always"
              @change="updateClimate"
              v-model="stPieterDischarge"
            ></v-slider>
            <v-slider
              inverse-label
              :min="0"
              :max="60"
              disabled
              label="Venlo waterlevel"
              thumb-label="always"
              v-model="venlo"
            ></v-slider>
            <v-slider
              inverse-label
              :min="0"
              :max="60"
              disabled
              label="Lith waterlevel"
              thumb-label="always"
              v-model="lith"
            ></v-slider>
          </v-card-text>
        </v-card>
      </v-tab-item>
      <v-tab-item key="slr" class="climate-scenario">
        <v-card>
          <v-card-text>
            <h2>Sea level</h2>
            <p>Raise the sea level in the port.</p>
            <v-slider
              :step="0.1"
              inverse-label
              :min="0"
              :max="2"
              vertical
              label="Sea level [m]"
              thumb-label="always"
              @change="updateClimate"
              v-model="sealevel"
            ></v-slider>
          </v-card-text>
        </v-card>
      </v-tab-item>
    </v-tabs>
  </div>
</template>
<script>
import { mapFields } from 'vuex-map-fields'
import { mapActions } from 'vuex'

export default {
  name: 'ClimateComponent',
  inject: ['bus'],
  components: {},
  data() {
    return {
      lobithDischarge: 2000,
      stPieterDischarge: 300,
      sealevel: 0.0
    }
  },
  methods: {
    ...mapActions(['computeWaterlevels']),
    updateClimate() {
      const climate = {
        // TODO: naming
        discharge_lobith: this.lobithDischarge,
        discharge_st_pieter: this.stPieterDischarge,
        sealevel: this.sealevel
      }
      this.computeWaterlevels(climate)
    }
  },
  computed: {
    ...mapFields(['waterlevels', 'velocities']),
    nijmegen: {
      get() {
        return this.lobithDischarge / 70
      },
      set(val) {}
    },
    kaub: {
      get() {
        return this.lobithDischarge / 80
      },
      set(val) {}
    },
    duisburg: {
      get() {
        return this.lobithDischarge / 50
      },
      set(val) {}
    },
    venlo: {
      get() {
        return this.stPieterDischarge / 70
      },
      set(val) {}
    },
    lith: {
      get() {
        return this.stPieterDischarge / 80
      },
      set(val) {}
    }
  }
}
</script>
<style scoped>
.climate-scenario {
  margin-top: 2em;
}
</style>
