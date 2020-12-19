<template>
  <div>
    <h2> Sites </h2>
    <v-card v-for="site in sites.features" :key="site.id">
      <v-card-title class="mb-4">
        {{ site.properties.name }}
        <v-spacer />
        <v-avatar size="20px">
          <img :src="harborIcon">
        </v-avatar>
      </v-card-title>
      <v-card-text>
        <v-slider
          v-if="site.properties.name === 'Maasvlakte'"

          :step="500"
          inverse-label
          :min="0"
          :max="30000"
          label="cargo in TEU/Tonne"
          thumb-label="always"

          v-model="site.properties.level"
        ></v-slider>
        <v-slider
          v-if="site.properties.name === 'Basel'"
          disabled
          :step="500"
          inverse-label
          :min="0"
          :max="30000"
          label="capacity in TEU/Tonne"
          thumb-label="always"

          v-model="site.properties.level"
        ></v-slider>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import harborIcon from '@mapbox/maki/icons/harbor-11.svg'

export default {
  data () {
    return {
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      harborIcon,
      draw: {}
    }
  },
  computed: {
    ...mapState(['sites'])
  }
}

</script>
