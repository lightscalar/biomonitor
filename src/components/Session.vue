<template>
  <v-container fluid class='ma-3'>

    <v-row class="">
      
      <v-col xs4 class="">

	<v-card class="">
	  <v-card-row class=''>
	    <v-card-title class='black white--text'>
	      {{currentSession.name}}
	    </v-card-title>
	  </v-card-row>
	  <v-card-row>
	    <v-card-text>
	      Collect data on the available channels.
	    </v-card-text>
	  </v-card-row>
	  <v-card-row actions >
	    <v-btn-toggle v-bind:options="toggle_options" 
 	      v-model="toggle_exclusive" class='text-xs-center'
	      @click.native='command'>
	    </v-btn-toggle>
	  </v-card-row>
	  

	</v-card>

      </v-col>

      <v-col xs8 class="">
	<data-chart :data='data'></data-chart>
	<v-btn primary @click.native='updateData'>Update Data</v-btn>
      </v-col xs8>
      
    </v-row>

  </v-container>
</template>

<script>
  
  // import Component from "../component_location"
  import DataChart from './DataChart'

  export default {
    
    props: ['id'],

    components: {DataChart},

    data() {
      return {
	data: [
	  {x: 1, y: 5}
	],
	toggle_exclusive: 2,
	toggle_options: [
	  { icon: 'mic', value: 1 },
	  { icon: 'mic_off', value: 2 },
	],
      }	
    },

    watch: {
      toggle_exclusive: function() {
	console.log('Commanding things now! ' + this.toggle_exclusive) 
	if (!this.toggle_exclusive) {
	  this.toggle_exclusive=2
	}
	if (this.toggle_exclusive == 1) {
	  this.$store.dispatch('startCollection')
	} else {
	  this.$store.dispatch('stopCollection')
	}
      } 
    },

    methods: {
      updateData() {
	var len = this.data.length
	var lastData = this.data[len-1]
	var newX = lastData.x + 1
	var newY = lastData.y + 10 * (Math.random()-0.5)
	this.data.push({x: newX, y: newY})
	len = this.data.length
	lastData = this.data[len-1]
	newX = lastData.x + 1
	newY = lastData.y + 10 * (Math.random()-0.5)
	this.data.push({x: newX, y: newY})
      },
      command() {
	console.log('Starting Collection') 
      }
    },

    computed: {
      currentSession() {
	return this.$store.state.currentSession
      }
    },

    mounted() {
      this.$store.dispatch('getSession', this.id)
      	
    }
  
  }

</script>


<style>
  
</style>

