<template>
  <v-container fluid class='ma-3'>

    <v-row class="">
      
      <v-col xs4 class="">

	<v-card>
	  <v-card-title class='blue-grey darken-2 white--text'>
	    {{currentSession.name}}
	    <v-spacer/>
	      <v-btn-toggle v-bind:options="toggle_options" 
		 v-model="toggle_exclusive" class='text-xs-center'
		 @click.native='command'>
	      </v-btn-toggle>
	    </v-card-title>

	  <v-card-row>
	  <v-card-text>
	    <v-container fluid>
	      <v-row>
		<v-col xs2>
		  <v-btn primary class='mt-3' icon='icon'>
		    <v-icon>play_arrow</v-icon>
		  </v-btn>
		</v-col>
		<v-col xs10>
		  <v-slider v-bind:thumb-label='true' v-bind:min='0' v-bind:max='100' v-bind:step='2'
		    append-icon='timelapse' v-model='selectedTime'></v-slider>
		</v-col>
	      </v-row>
	    </v-container>
	  </v-card-text>
	  </v-card-row>
	</v-card>
	

	</v-col>

	<v-col xs8>
	  <v-card id='data-1' v-for='channel in currentSession.channels'
	      key = 'channel.physicalChannel'>
	    <v-card-title class='blue-grey darken-2 white--text'>
	      {{channel.description}}
	      <v-spacer/>
		<v-btn icon='icon'><v-icon>insert_comment</v-icon></v-btn>
	    </v-card-title>
	    <v-card-row>
	      <smooth-chart
		:channel='channel.physicalChannel' 
		:reset='resetChart'
		:dataHistory='historicalData(channel.physicalChannel)'
		:data='channelData(channel.physicalChannel)'>
	      </smooth-chart>
	    </v-card-row>
	  </v-card>
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
	selectedTime: 0,
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
      historicalData(channelRequest) {
	var data = this.$store.state.dataHistory 
	for (var k=0; k<data.length; k++) {
	  if (data[k].physicalChannel == channelRequest) {
	    return data[k].data
	  }
	}
	return [] 
      }
    },

    computed: {
      currentSession() {
	return this.$store.state.currentSession
      },
      totalDuration() {
	var data = this.$store.state.dataHistory
	if (data.length>0) {
	  var len = data[0].data.length
	  return data[0].data[len-1][0]
	} else {
	  return 0
	}
      }
    },

    mounted() {
      // Load the current session.
      this.$store.dispatch('getSession', this.id)

      // Load historical session data.
      // this.$store.dispatch('getHistory', {id: this.id})
    }
  
  }

</script>


<style>
  
</style>

