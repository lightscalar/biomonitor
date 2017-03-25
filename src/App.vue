<template>
  <v-app id="app">
    <v-toolbar class="grey lighten-4">
      <a href='/#'>
	<img src='./assets/bio_logo@2x.png' class='logo'>
      </a>
      <v-spacer/>
      <connection-modal class="" v-if='deviceStatus.isConnected'>
      </connection-modal>
      <v-btn dark error flat v-else @click.native="showMessage=true">
	<v-icon class='mr-2'>error</v-icon>
	Device Not Connected
      </v-btn>
      <v-snackbar v-model='showMessage'>
	{{statusMessage}}
	<v-btn flat class="pink--text" @click.native="showMessage=false">
	  Close
	</v-btn>
      </v-snackbar>
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
	modal: false,
	showMessage: false
      }
    },
    computed: {
      deviceStatus() {
	return this.$store.state.deviceStatus
      },
      statusMessage() {
	return this.$store.state.deviceStatus.statusMessage 
      }
    },
    methods: {
      checkStatus() {
        this.$store.dispatch('checkStatus')
      }
    },
     
    mounted() {
      this.checkStatus()
      // setInterval(this.checkStatus, 2000)
    }
  }
</script>

<style>
  .logo {
    height: 40px;
  }
</style>
