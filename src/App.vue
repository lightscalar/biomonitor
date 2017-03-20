<template>
  <v-app id="app">
    <v-toolbar class="grey lighten-4">
      <a href='/#'>
	<img src='./assets/bio_logo@2x.png' class='logo'>
      </a>
      <v-spacer/>
      <connection-modal class="">
        
      </connection-modal>
    </v-toolbar>
    <router-view></router-view>
  </v-app>
</template>

<script>
  import ConnectionModal from './components/ConnectionModal.vue'
  export default {
    name: 'app',
    components: {ConnectionModal},
    data() {
      return {
	modal: false
      } 
    }
  }
</script>

<style>
.logo {
  height: 40px;
}

</style>
