<template>
<div>
  <v-tabs
    >
    <v-tab
      :key="discharge">
      Discharge
    </v-tab>
    <v-tab
      :key="vc">
      Vertical clearance
    </v-tab>
    <v-tab
      :key="sl">
      Sea level
    </v-tab>

    <v-tab-item
      :key="discharge"
      class="climate-scenario"
      >
      <v-card outlined>
        <v-card-text>
          <h2>Discharge</h2>
          <p>In/decrease the discharge at Lobith. This influences water depths and currents over the whole river.</p>
          <v-slider
            :step="1000"
            inverse-label
            :min="1000"
            :max="15000"
            label="Rhine discharge"
            thumb-label="always"
            v-model="discharge"
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
    </v-tab-item>
    <v-tab-item
      :key="ad"
      class="climate-scenario"
      >
      <v-card>
        <v-card-text>
          <h2>Vertical clearance</h2>
          <p>Set the vertical clearance to a fixed level.</p>
          <v-slider
            :step="0.5"
            inverse-label
            :min="2"
            :max="15"
            label="Vertical clearance"
            thumb-label="always"
            v-model="verticalClearance"
            ></v-slider>
        </v-card-text>
      </v-card>

    </v-tab-item>
    <v-tab-item
      :key="slr"
      class="climate-scenario"
      >
      <v-card>
        <v-card-text>
          <h2>Sea level</h2>
          <p>Raise the sea level in the port.</p>
          <v-slider
            :step="0.5"
            inverse-label
            :min="0"
            :max="2"
            label="Sea level"
            thumb-label="always"
            v-model="seaLevel"
            ></v-slider>
        </v-card-text>

      </v-card>

      </v-tab-item>

    </v-tabs>
  </div>
</template>
<script>
export default {
  name: 'ClimateComponent',
  data () {
    return {
      discharge: 8000,
      verticalClearance: 6,
      seaLevel: 0.0
    }
  },
  computed: {
    nijmegen: {
      get () {
        return this.rhine / 70
      },
      set (val) {

      }
    },
    kaub: {
      get () {
        return this.rhine / 80
      },
      set (val) {

      }
    },
    duisburg: {
      get () {
        return this.rhine / 50
      },
      set (val) {

      }
    }

  }
}
</script>
<style scoped>
.climate-scenario {
  margin-top: 2em;
}
</style>
