<template>
  <div>
    <div v-show="events.length === 0">
      <v-progress-circular
        indeterminate
        color="primary"
      ></v-progress-circular>

    </div>
    <div v-show="events.length > 0">
      <v-slider
        v-model="shipState"
        :thumb-size="24"
        thumb-label="always"
        :max="events.length"
        :prepend-icon="play ? 'mdi-pause' : 'mdi-play'"
        @click:prepend='play = !play'
        @change="onChange"
        class="d-flex-grow pt-6"
      >
        <v-avatar size="50px">
          <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRvKRniAxUXUWzmByw7CRFYD5fTqOtFTDVkw&usqp=CAU">
        </v-avatar>
      </v-slider>
      <div class="fleets pa-0 pr-2">
        <v-timeline
          class="fleets pa-0 pr-2"
          dense
          clipped
        >
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
                <v-col cols="7">
                  {{event.properties.Description}}
                </v-col>
                <v-col
                  class="text-right"
                  cols="5"
                >
                  {{event.properties.Start}}
                </v-col>
              </v-row>
            </v-timeline-item>
        </v-timeline>
      </div>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'
import { mapState, mapMutations } from 'vuex'

export default {
  data: () => ({
    input: null,
    nonce: 0
  }),

  computed: {
    ...mapState(['results', 'currentTime']),
    play: {
      get () { return this.$store.state.play },
      set (value) { this.setPlay(value) }
    },
    shipState: {
      get () { return this.$store.state.shipState },
      set (value) { this.setShipState(value) }
    },
    events () {
      return _.get(this.results, 'log.features', [])
    }
  },

  watch: {
    shipState (value) {
      const ref = this.$refs[`event-${value}`]

      if (ref && ref[0]) {
        const { $el } = ref[0]

        $el.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })
      }
    }
  },

  methods: {
    ...mapMutations(['setPlay', 'setShipState']),
    eventColor (event) {
      const colors = {
        Ship: 'blue',
        Port: 'green',
        Operator: 'purple'
      }
      return colors[event.properties.Actor] || 'grey'
    },
    checkIfActive (event) {
      return this.currentTime >= event.properties['Start Timestamp']
    },
    onChange (event) {
      console.log(event)
    }
  }
}
</script>

<style>
  .fleets {
    max-height: 50vh;
    overflow-y: auto;
    overflow-x: hidden;
  }
</style>
