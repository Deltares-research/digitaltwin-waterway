<template>
  <div>
    <v-card class="mb-4">
      <v-card-title>Results</v-card-title>

      <div v-if="events.length === 0" class="py-8 w-full d-flex align-center justify-center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </div>
      <div v-if="results.env && events.length > 0">
        <v-slider
          :value="progress"
          :thumb-size="24"
          :min="0"
          :max="1"
          :step="0.01"
          :prepend-icon="play ? 'mdi-pause' : 'mdi-play'"
          @click:prepend="play = !play"
          @input="onInput"
          @mousedown="onMousedown"
          @mouseup="onMouseup"
          class="d-flex-grow pt-6"
        />
        <div class="fleets pa-0 pr-2">
          <v-timeline dense clipped>
            <v-timeline-item
              v-for="event in events"
              :key="event.id"
              :ref="`event-${event.id}`"
              :color="eventColor(event)"
              class="mb-4"
              icon-color="grey lighten-2"
              small
            >
              <v-row
                :class="{
                  'font-weight-bold': checkIfActive(event)
                }"
                justify="space-between"
              >
                <v-col cols="7">{{event.properties.Description}}</v-col>
                <v-col class="text-right" cols="5">{{event.properties.Start}}</v-col>
              </v-row>
            </v-timeline-item>
          </v-timeline>
        </div>
      </div>
    </v-card>
    <v-card class="mb-4">
      <v-card-title>Model input</v-card-title>
      <v-card-actions>
        <v-btn text @click="exportConfig">Export</v-btn>
      </v-card-actions>
    </v-card>
    <v-card class="mb-4">
      <v-card-title>Model output</v-card-title>
      <v-card-actions>
        <v-btn text @click="exportResult">Export</v-btn>
      </v-card-actions>
    </v-card>

    <!-- Export button (for all scenario json info) -->
  </div>
</template>
<script>
import _ from 'lodash'
import { mapState, mapMutations } from 'vuex'
import { saveAs } from 'file-saver'

export default {
  props: {
    config: Object
  },
  data: () => ({
    input: null,
    nonce: 0
  }),

  computed: {
    ...mapState(['results', 'currentTime', 'progress', 'play']),
    play: {
      get() {
        return this.$store.state.play
      },
      set(value) {
        this.setPlay(value)
      }
    },
    events() {
      const events = _.get(this.results, 'log.features', [])

      // add custom events for start & end of simulation
      return events.length
        ? [
            {
              id: 'start',
              properties: {
                Description: 'Start simulation',
                Name: 'Start',
                Start: this.results.env.epoch_iso,
                'Start Timestamp': this.results.env.epoch,
                Stop: this.results.env.epoch_iso,
                'Stop Timestamp': this.results.env.epoch
              }
            },
            ...events,
            {
              id: 'stop',
              properties: {
                Description: 'Stop simulation',
                Name: 'Stop',
                Start: this.results.env.now_iso,
                'Start Timestamp': this.results.env.now,
                Stop: this.results.env.now_iso,
                'Stop Timestamp': this.results.env.now
              }
            }
          ]
        : []
    },
    activeEvent() {
      const activeEvents = this.events
        .filter((event) => {
          return (
            this.currentTime >= event.properties['Start Timestamp'] &&
            this.currentTime < event.properties['Stop Timestamp']
          )
        })
        .map(({ id }) => parseInt(id))
        .sort((a, b) => b - a)

      return activeEvents[0]
    }
  },

  watch: {
    activeEvent(value) {
      this.scrollEventIntoView(value)
    }
  },

  methods: {
    ...mapMutations(['setPlay', 'setProgress']),
    eventColor(event) {
      const colors = {
        Ship: 'blue',
        Port: 'green',
        Operator: 'purple'
      }
      return colors[event.properties.Actor] || 'grey'
    },
    checkIfActive(event) {
      return this.currentTime >= event.properties['Start Timestamp']
    },
    scrollEventIntoView: _.debounce(function (value) {
      const ref = this.$refs[`event-${value}`]

      if (ref && ref[0]) {
        const { $el } = ref[0]

        $el.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })
      }
    }, 200),
    onMousedown() {
      // store if timeline was playing so we can either start playing
      // or not when dragging ends
      this.wasPlaying = this.play
      this.setPlay(false)
    },
    onMouseup() {
      // use stored playing state to start playing or not
      this.setPlay(this.wasPlaying)
    },
    onInput(value) {
      this.setProgress(value)
    },
    exportConfig() {
      var blob = new Blob([JSON.stringify(this.config)], {
        type: 'application/json;charset=utf-8'
      })
      saveAs(blob, 'config.geojson')
    },
    exportResult() {
      var blob = new Blob([JSON.stringify(this.results)], {
        type: 'application/json;charset=utf-8'
      })
      saveAs(blob, 'result.json')
    }
  }
}
</script>

<style>
.fleets {
  overflow-y: auto;
  overflow-x: hidden;
  max-height: 50vh;
}
</style>
