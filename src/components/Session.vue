<template>
  <v-container fluid class='ma-3'>

    <v-row class="">
      
      <v-col xs3 class="">

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


      <!-- EPOCH.JS PLOTS -->
      <v-col xs9>

	<v-row v-for='channel in currentSession.channels'
	       key='channel.physicalChannel'>
	  
	  <v-card style='width:100%'>
	    <v-card-title>
	      {{channel.description}}
	    </v-card-title>
	    <smooth-chart
	      :channel='channel.physicalChannel' 
	      :reset='resetChart'
	      :data='channelData(channel.physicalChannel)'>
	    </smooth-chart>
	  </v-card>

	</v-row>

      </v-col>

    </v-row>

  </v-container>
</template>

<script>
  
  // import Component from "../component_location"
  import DataChart from './DataChart'
  import FastChart from './FastChart'
  import SmoothChart from './SmoothChart'

  export default {
    
    props: ['id'],

    components: {DataChart, FastChart, SmoothChart},

    data() {
      return {
	dataInterval: null,
	resetChart: false,
	maxTime: 0,
	latestTimestamp: 0,
	recording: false,
	toggle_exclusive: 2,
	toggle_options: [
	  { icon: 'mic', value: 1 },
	  { icon: 'mic_off', value: 2 },
	],
      }	
    },

    watch: {
      toggle_exclusive: function() {
	if (!this.toggle_exclusive) {
	  this.toggle_exclusive=2 // By default, we're not recording.
	  this.recording= false
	}
	if (this.toggle_exclusive == 1) {
	  var data = {id: this.id, cmd: "start"}
	  this.$store.dispatch('sessionCommand', data)
	  this.recording = true
	  this.dataInterval = setInterval(this.getData, 1000)
	  this.resetChart=true
	} else {
	  var data = {id: this.id, cmd: "stop"}
	  this.$store.dispatch('sessionCommand', data)
	  clearInterval(this.dataInterval)
	  this.dataInterval = null
	  this.resetChart=false
	}
      } 
    },

    methods: {
      getData() {
	this.$store.dispatch('updateStream', 
	  {id: this.id, minTime: -1, maxTime:-1})
      },
      channelData(channelRequest) {
	var data = this.$store.state.currentData
	for (var k=0; k<data.length; k++) {
	  if (data[k].physicalChannel == channelRequest) {
	    return data[k].data
	  }
	}
	return [] 
      },
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

