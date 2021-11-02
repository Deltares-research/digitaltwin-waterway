<template>
  <div class="ship" :style="shipStyle" :title="name">
    <v-avatar :size="size * 0.9" class="avatar" :color="avatarColor">
      <img :src="imgUrl" />
    </v-avatar>
    <v-progress-circular :rotate="270" :value="progress" :size="size" :color="progressColor"></v-progress-circular>
  </div>

</template>

<script>
export default {
  name: 'EquipmentIcon',
  props: {
    progress: {
      type: Number,
      default: 0
    },
    avatarColor: {
      type: String,
      default: 'rgba(255, 255, 255, 0.8)'
    },
    progressColor: {
      type: String,
      default: 'pink'
    },
    shipImage: {
      type: String
    },
    size: {
      type: Number,
      default: 50
    },
    // allow to access a mapboxMarker if provided
    mapboxMarker: {
      type: Object,
      required: false
    },
    // any type is fine
    name: [String, Number]
  },
  computed: {
    shipStyle () {
      return {
        width: this.size + 'px',
        height: this.size + 'px'
      }
    },
    showBadge () {
      return !!this.badge
    },
    imgUrl () {
      return this.shipImage || 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRvKRniAxUXUWzmByw7CRFYD5fTqOtFTDVkw&usqp=CAU'
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
.ship {
  position: relative;
}
.v-progress-circular__overlay {
  transition: initial !important;
}
.ship .avatar {
  font-weight: 200;
  top: 5%;
  left: 5%;
  position: absolute;
}
</style>
