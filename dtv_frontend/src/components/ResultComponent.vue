<template>
  <div>
    <v-slider
      v-model="shipState"
      :thumb-size="24"
      thumb-label="always"
      :max="events.length"
      :prepend-icon="play ? 'mdi-pause' : 'mdi-play'"
      @click:prepend='play = !play'
      class="d-flex-grow pt-6"
    >
      <v-avatar size="50px">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRvKRniAxUXUWzmByw7CRFYD5fTqOtFTDVkw&usqp=CAU">
      </v-avatar>
    </v-slider>
    <v-timeline
      class="fleets pa-0 pr-2"
      dense
      clipped
    >
    <div
      v-for="event in events"
      :key="event.id"
      >
      <v-timeline-item
        class="mb-4"
        :color="eventColor(event)"
        icon-color="grey lighten-2"
        small
      >
        <v-row justify="space-between">
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
      </div>
    </v-timeline>
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
    ...mapState(['results']),
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
  methods: {
    ...mapMutations(['setPlay', 'setShipState']),
    eventColor (event) {
      const colors = {
        Ship: 'blue',
        Port: 'green',
        Operator: 'purple'
      }
      return colors[event.properties.Actor] || 'grey'
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
