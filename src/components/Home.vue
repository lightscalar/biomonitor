<template>

  <v-content v-if='isConnected'>
    <v-container fluid class='ma-2'>
      <v-row>
	<v-col xs2='xs2'>
	</v-col>
	<v-col xs8='xs8'>

	  <v-alert error v-bind:value="true" class='mt-5'>
	    Device is not attached. Please attach device and select the correct
	    serial port.
	  </v-alert>

	</v-col>
      </v-row>
    </v-container> 
  </v-content>

  <v-content v-else>
    <create-session></create-session>
  </v-content>

</template>

<script>

  // import Component from "../component_location"
  import CreateSession from "./CreateSession.vue"

  export default {

    components: {CreateSession},

    data() {
      return {

      }	
    },

    computed: {
      isConnected() {
	var devicePort = this.$store.state.devicePort
	return (devicePort === null)
      } 
    },

    methods: {

    },

    mounted() {

    }

  }

  </script>


  <style>
  .top {
    margin-top:25px
  }
  </style>

