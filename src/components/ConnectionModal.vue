<template>
  <div>
    <v-modal v-model="modal">
      <v-btn slot='activator' dark primary flat>
	<v-icon class="mr-2">
	  device_hub
	</v-icon>
	<v-spacer/>
	  <div v-if='devicePort'>
	    {{devicePort}}
	  </div>
	  <div v-else>
	    Attach Device
	  </div>
	</v-btn>
	<v-card>
	  <v-card-text>
	    <h2 class="title primary--text">Select Device</h2>
	  </v-card-text>
	  <v-card-text class="subheading grey--text">

	    <v-select 
		v-bind:items="availableDevices"
		v-model="selectedDevice"
		label="Select Device"
		v-on:change='didIt()'
		light
		single-line/>

	    </v-card-text>
	  <v-card-row actions>
	    <v-spacer></v-spacer>
	    <v-btn flat v-on:click.native="modal=false" 
		class="red--text accent-1--text">
	      <v-icon class="mr-2">
	        cancel
	      </v-icon>
	      Cancel
	    </v-btn>
	    <v-btn flat v-on:click.native="attachDevice" 
		class="primary--text">
	      <v-icon class="mr-2">
	        done
	      </v-icon> 
	      Attach
	    </v-btn>
	  </v-card-row>
	</v-card>
      </v-modal> 
  </div>
</template>

<script>
  
  // import Component from "../component_location"

  export default {
    
    components: {},

    data() {
      return {
	modal: false,
	selectedDevice: null
      }	
    },

    computed: {
      availableDevices() {
	var devices = this.$store.state.deviceStatus.availableDevices
	return utils.itemize(devices)
      },
      devicePort() {
	return this.$store.state.devicePort 
      }
    },

    methods: {
      attachDevice() {
	this.$store.commit('attachDevice', this.selectedDevice.text)
	this.modal = false
      }  	
    },

    mounted() {

    }
  
  }

</script>

<style>
  
</style>

