<template>
  <div>
    <v-card class="mb-3">
      <v-card-title>Duration variation</v-card-title>
      <v-card-text>
        <!-- <v-chip>Max trip duration: 35 hours</v-chip> -->
        <v-sheet color="grey darken-2 mt-3" elevation="5" class="chart">
          <v-chart class="chart" :option="chartTripDuration" :init-options="initOptions" />
        </v-sheet>
      </v-card-text>
    </v-card>
    <v-card class="mb-3">
      <v-card-title>Duration breakdown</v-card-title>
      <v-card-text>
        <!-- <v-chip>Duration: 10 days 3 hours</v-chip> -->
        <v-sheet color="grey darken-2 mt-3" elevation="5" class="chart">
          <v-chart class="chart" :option="chartDurationBreakdown" :init-options="initOptions" />
        </v-sheet>
      </v-card-text>
    </v-card>
    <v-card class="mb-3">
      <v-card-title>Trips</v-card-title>
      <v-card-text>
        <!-- <v-chip># Trips: 30</v-chip> -->
        <v-sheet class="chart">
          <v-chart class="chart" :option="chartTripHistogram" :init-options="initOptions"></v-chart>
        </v-sheet>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-title>Gantt</v-card-title>
      <v-card-text>
        <v-sheet>
          <div id="gantt"></div>
        </v-sheet>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title>Energy by Distance</v-card-title>
      <v-card-text>
        <v-sheet class="chart">
          <v-chart class="chart" :option="chartEnergyByDistance" :init-options="initOptions"></v-chart>
        </v-sheet>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-title>Energy by Time</v-card-title>
      <v-card-text>
        <v-sheet class="chart">
          <v-chart class="chart" :option="chartEnergyByTime" :init-options="initOptions"></v-chart>
        </v-sheet>
      </v-card-text>
    </v-card>

    <h2>The following indicators are not available yet</h2>
    <v-card>
      <v-card-text>
        <h2>Fuel consumption</h2>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-text>
        <h2>Total emissions</h2>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-text>
        <h2>Ton KM</h2>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-text>
        <h2>Occupancy</h2>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-text>
        <h2>Deadhead share</h2>
      </v-card-text>
    </v-card>
  </div>
</template>
<script>
import { mapState } from 'vuex'
import { THEME_KEY } from 'vue-echarts'
import Plotly from 'plotly.js'

export default {
  data() {
    return {
      initOptions: {
        renderer: 'svg'
      }
    }
  },
  provide: {
    [THEME_KEY]: 'dark'
  },
  async mounted() {},
  computed: {
    ...mapState([
      'chartTripDuration',
      'chartDurationBreakdown',
      'chartTripHistogram',
      'chartGantt',
      'chartEnergyByDistance',
      'chartEnergyByTime'
    ])
  },

  watch: {
    chartGantt(options) {
      // set gantt chart
      console.log('Plotly', Plotly)
      Plotly.react('gantt', options)
    }
  },

  methods: {}
}
</script>

<style>
.chart {
  height: 400px;
  width: 700px;
}
</style>
