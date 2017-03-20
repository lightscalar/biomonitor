<template>
  <div>
    <v-modal v-model="modal">
      <v-btn slot='activator' dark primary flat>
	<v-icon class="mr-2">
	  device_hub
	</v-icon>
	<v-spacer/>
	  Connect
	</v-btn>
	<v-card>
	  <v-card-text>
	    <h2 class="title primary--text">Connect to a biomonitor</h2>
	  </v-card-text>
	  <v-card-text class="subheading grey--text">

	    <v-select 
		v-bind:items="states"
		v-model="port"
		label="Select Serial Port"
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
	    <v-btn flat v-on:click.native="modal=false" 
		class="primary--text">
	      <v-icon class="mr-2">
	        done
	      </v-icon> 
	      Connect
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
	states: [{text:'/dev/tty.usbserial-FT9J9DNE'}, {text: '/dev/tty.usbserial-FH9H9DNF'}],
	port: {}
      }	
    },

    methods: {
      	
    },

    mounted() {
      	
    }
  
  }

</script>

<style>
  
</style>

