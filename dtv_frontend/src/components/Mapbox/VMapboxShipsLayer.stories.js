import VMapboxShipsLayer from './VMapboxShipsLayer.vue'
import VMapboxSiteLayer from './VMapboxSiteLayer.vue'
import mockData from './mock/data.json'
import sitesMockData from './mock/sites.json'

export default {
  component: VMapboxShipsLayer,
  title: 'Components/VMapboxShipsLayer',
  argTypes: {
    play: {
      control: { type: 'boolean' }
    }
  }
}

const Template = (args) => ({
  components: { VMapboxShipsLayer, VMapboxSiteLayer },
  data () {
    return {
      ...args,
      play: false,
      progress: 0
    }
  },
  template: `
    <div>
      <button @click="play = true">play</button>
      <button @click="play = false">pause</button>
      <input type="range" min="0" max="100" v-model="progress" />
      {{ progress }}
      <v-mapbox
        style="width:80vw;height:80vh"
        id="map"
        ref="map"
        :zoom="5"
        :center="[6, 50]"
        :logoPosition="'bottom-right'"
        :preserve-drawing-buffer="true"
        :trackResize="'false'"
        access-token="${process.env.VUE_APP_MAPBOX_TOKEN}"
        map-style="mapbox://styles/global-data-viewer/cjtss3jfb05w71fmra13u4qqm"
      >
        <v-mapbox-site-layer
          v-if="sites.features"
          :sites="sites"
        />
        <v-mapbox-ships-layer
          v-if="response.log.features.length > 0"
          :tStart="response.env.epoch"
          :tStop="response.env.now"
          :results="response"
          :sites="sites"
          :play="play"
          :progress="progress / 100"
          @change="$event => progress = $event"
        />
      </v-mapbox>
    </div>
  `
})

export const Primary = Template.bind({})

Primary.args = {
  response: mockData,
  sites: sitesMockData
}
