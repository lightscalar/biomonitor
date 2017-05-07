<template>
  <v-app id="app">
    <v-toolbar class="elevation-0 blue-grey darken-4">

      <a href='/#'>
	<img src='./assets/bio_logo@2x.png' class='logo'>
      </a>
      <v-spacer/>

	<v-btn primary v-if='deviceStatus.isConnected' class='elevation-0'>
	  <v-icon class='mr-2'>check_circle</v-icon>
	  {{deviceStatus.statusMessage}}
	</v-btn>

	<v-btn warning light v-else @click.native="checkStatus" 
	       class='elevation-0'>
	  <v-icon class='mr-2'>error</v-icon>
	  {{deviceStatus.statusMessage}}
	</v-btn>

	<v-snackbar v-model='showMessage'>
	{{statusMessage}}
	<v-btn flat class="pink--text" @click.native="showMessage=false">
	  Close
	</v-btn>
      </v-snackbar>

    </v-toolbar>

    <div id='chart'></div>

    <router-view></router-view>
  </v-app>
</template>

<script>

  export default {
    name: 'app',
    components: {},
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
