<template>
  <div>
    <v-card class="mb-3">
      <v-card-title>Duration variation</v-card-title>
      <v-card-text>
        <v-chip>Max trip duration: 35 hours</v-chip>

        <v-sheet color="grey darken-2 mt-3" elevation="5" class="chart">
          <v-chart class="chart" :option="durationVariationOption" :init-options="initOptions" />
        </v-sheet>
      </v-card-text>
    </v-card>
    <v-card class="mb-3">
      <v-card-title>Duration breakdown</v-card-title>
      <v-card-text>
        <v-chip>Duration: 10 days 3 hours</v-chip>
        <v-sheet color="grey darken-2 mt-3" elevation="5" class="chart">
          <v-chart class="chart" :option="durationOption" :init-options="initOptions" />
        </v-sheet>
      </v-card-text>
    </v-card>
    <v-card class="mb-3">
      <v-card-title>Trips</v-card-title>
      <v-card-text>
        <v-chip># Trips: 30</v-chip>
        <v-sheet class="chart">
          <v-chart class="chart" :option="tripsOption" :init-options="initOptions"></v-chart>
        </v-sheet>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-title>Gantt</v-card-title>
      <v-card-text>
        <v-chip># Trips: 30</v-chip>
        <v-sheet>
          <v-img src="graphics/gantt.png"></v-img>
        </v-sheet>
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
    <v-card>
      <v-card-text>
        <h2>Total Energy</h2>
      </v-card-text>
    </v-card>
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
  </div>
</template>
<script>
import { THEME_KEY } from 'vue-echarts'
export default {
  data() {
    return {
      initOptions: {
        renderer: 'svg'
      },
      durationOption: {},
      durationVariationOption: {},
      tripsOption: {}
    }
  },
  provide: {
    [THEME_KEY]: 'dark'
  },
  async mounted() {
    const durationResponse = await fetch('data/results/duration.json')
    this.durationOption = await durationResponse.json()
    const durationVariationResponse = await fetch(
      'data/results/duration-variation.json'
    )
    this.durationVariationOption = await durationVariationResponse.json()
    const tripsResponse = await fetch('data/results/trips.json')
    this.tripsOption = await tripsResponse.json()
  },
  computed: {},

  watch: {},

  methods: {}
}
</script>

<style>
.chart {
  height: 400px;
  width: 700px;
}
</style>
