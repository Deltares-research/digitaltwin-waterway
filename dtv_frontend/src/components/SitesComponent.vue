<template>
  <div>
    <v-card class="mb-4">
      <v-card-title>Cargo type</v-card-title>
      <v-card-text>
        <v-select :items="cargoTypes" v-model="cargoType"></v-select>
      </v-card-text>
    </v-card>
    <div></div>

    <div v-if="cargoType">
      <v-card class="mb-4">
        <v-card-title>Waypoints</v-card-title>
        <v-card-text>
          <div>Select waypoints by clicking on the graph in the map.</div>
          <v-timeline align-top dense v-show="waypoints.length">
            <v-timeline-item v-for="(waypoint, $index) in waypoints" :key="waypoint.id" small>
              <template v-slot:icon>
                <span>{{$index}}</span>
              </template>
              <v-form>
                <v-container class="pa-0">
                  <v-row>
                    <v-col cols="4">
                      <v-text-field label="id" disabled v-model="waypoint.properties.n"></v-text-field>
                    </v-col>
                    <v-col cols="6">
                      <v-text-field
                        label="name"
                        v-model="waypoint.properties.name"
                        placeholder="name"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="1">
                      <v-btn @click="removeWaypoint({index: $index})">
                        <v-icon small>mdi-delete</v-icon>
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-container>
              </v-form>
            </v-timeline-item>
          </v-timeline>
        </v-card-text>
      </v-card>
    </div>

    <div v-if="cargoType && startSite">
      <v-card class="mb-4">
        <v-img height="200" :src="siteImg(startSite)" class="site-sat-image"></v-img>
        <v-card-title>
          Configure start site
          <v-spacer />
          <v-avatar size="20px">
            <img :src="harborIcon" />
          </v-avatar>
        </v-card-title>
        <v-card-subtitle>{{ startSite.properties.name }}</v-card-subtitle>
        <v-card-text>
          <v-form>
            <v-slider
              :step="capacityStep"
              :min="0"
              :max="maxCapacity"
              persistent-hint
              :hint="unit"
              label="Cargo capacity"
              thumb-label="always"
              v-model="startSite.properties.capacity"
            ></v-slider>
            <v-slider
              :step="capacityStep"
              :min="0"
              :max="startSite.properties.capacity"
              persistent-hint
              :hint="unit"
              label="Cargo level"
              thumb-label="always"
              v-model="startSite.properties.level"
            ></v-slider>
            <v-slider
              :step="loadingRateStep"
              :min="0"
              :max="maxLoadingRate"
              :hint="unit + ' / hour'"
              label="Loading rate"
              persistent-hint
              thumb-label="always"
              v-model="startSite.properties.loadingRate"
            ></v-slider>
            <v-slider
              :step="loadingRateStep"
              :min="0"
              :max="maxLoadingRateVariation"
              label="Loading rate variation"
              persistent-hint
              :hint="unit + ' / hour'"
              thumb-label="always"
              v-model="startSite.properties.loadingRateVariation"
            ></v-slider>
          </v-form>
        </v-card-text>
      </v-card>
    </div>

    <div v-if="cargoType && endSite">
      <v-card class="mb-4">
        <v-img height="200" :src="siteImg(endSite)" class="site-sat-image"></v-img>

        <v-card-title>
          Configure end site
          <v-spacer />
          <v-avatar size="20px">
            <img :src="harborIcon" />
          </v-avatar>
        </v-card-title>
        <v-card-subtitle>{{ endSite.properties.name }}</v-card-subtitle>
        <v-card-text>
          <v-form>
            <v-slider
              :step="loadingRateStep"
              :min="0"
              :max="maxLoadingRate"
              :hint="unit + ' / hour'"
              label="Loading rate"
              persistent-hint
              thumb-label="always"
              v-model="endSite.properties.loadingRate"
            ></v-slider>
            <v-slider
              :step="loadingRateStep"
              :min="0"
              :max="maxLoadingRateVariation"
              label="Loading rate variation"
              persistent-hint
              :hint="unit + ' / hour'"
              thumb-label="always"
              v-model="endSite.properties.loadingRateVariation"
            ></v-slider>
          </v-form>
        </v-card-text>
      </v-card>
    </div>

    <div v-if="cargoType && route.properties">
      <route-card :route="route"></route-card>
    </div>
  </div>
</template>

<script>
import harborIcon from '@mapbox/maki/icons/harbor-11.svg'
import markerIcon from '@mapbox/maki/icons/marker-11.svg'
import RouteCard from './RouteCard'
import { mapFields } from 'vuex-map-fields'
import { mapActions, mapGetters } from 'vuex'
import _ from 'lodash'

export default {
  inject: ['bus'],
  components: {
    RouteCard
  },
  data() {
    return {
      cargoTypes: ['Dry Bulk', 'Container'],
      mapboxAccessToken: process.env.VUE_APP_MAPBOX_TOKEN,
      harborIcon,
      markerIcon,
      map: null,
      draw: {}
    }
  },
  methods: {
    ...mapActions(['addWaypoint', 'removeWaypoint']),
    siteImg(site) {
      const server = 'https://api.mapbox.com'
      const token = this.mapboxAccessToken
      const lon = site.geometry.coordinates[0]
      const lat = site.geometry.coordinates[1]
      const style = 'satellite-v9'
      const pin = `pin-s+555555(${lon},${lat})`
      const url = `${server}/styles/v1/mapbox/${style}/static/${pin}/${lon},${lat},13,0,60/500x200@2x?access_token=${token}`
      return url
    }
  },
  created() {
    this.bus.on('map', (map) => {
      console.log('got map', map)
      this.map = map
    })
  },
  computed: {
    ...mapFields([
      'cargoType',
      'sites',
      'waypoints',
      'route',
      'selectedWaypoint'
    ]),
    ...mapGetters(['unit']),
    startSite() {
      return this.waypoints[0]
    },
    endSite() {
      if (this.waypoints.length < 2) {
        return null
      }
      return _.last(this.waypoints)
    },
    valid() {
      return this.waypoints.length >= 2
    },
    maxCapacity() {
      let maxCapacity = 1000
      if (this.unit === 'TEU') {
        maxCapacity = 1e4
      } else if (this.unit === 'Tonne') {
        maxCapacity = 1e5
      }
      return maxCapacity
    },
    maxLoadingRate() {
      let maxLoadingRate = 400
      if (this.unit === 'TEU') {
        maxLoadingRate = 60
      }
      if (this.unit === 'Tonne') {
        maxLoadingRate = 600
      }
      return maxLoadingRate
    },
    maxLoadingRateVariation() {
      return this.maxLoadingRate / 2
    },
    capacityStep() {
      return this.maxCapacity / 100
    },
    loadingRateStep() {
      return this.maxLoadingRate / 100
    }
  }
}
</script>
<style>
.site-sat-image {
  filter: saturate(0);
}
</style>
