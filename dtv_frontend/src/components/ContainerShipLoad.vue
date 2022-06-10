<template>
  <div class="container-ship-load">
    <svg>
      <defs>
        <div v-html="containerShip"></div>
      </defs>
      <use x="0" y="0" xlink:href="container-ship.svg#Container"/>
    </svg>
  </div>
</template>

<script>
import containerShip from 'container-ship.svg'

export default {
  name: 'ContainerShipLoad',
  props: {

  },
  data() {
    return {
      containerShip
    }
  },
  computed: {

  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
</style>
