<template>
  <v-container fluid class='ma-3'>

    <v-row class="">
      
      <v-col xs4 class="">

	<v-card>
	  <v-card-title class='blue-grey darken-2 white--text'>
	    {{currentSession.name}}
	    <v-spacer/>
	      <v-btn icon='icon' error v-if='recording' 
		v-tooltip:left="{ html: 'Pause Data Recording' }"
		@click.native='stopRecording'>
		<v-icon error>pause</v-icon>
	      </v-btn>
	      <v-btn icon='icon' error 
		v-tooltip:left="{ html: 'Start Data Recording' }"
		v-else @click.native='startRecording'>
		<v-icon error>fiber_manual_record</v-icon>
	      </v-btn>
	    </v-card-title>

	  <v-card-row>
	  <v-card-text>
	    <v-container fluid>
	      <v-row>
		<v-col xs2>
		  <v-btn primary class='mt-3' icon='icon' v-if='streaming'
		    @click.native='stopPlaying'>
		    <v-icon>pause</v-icon>
		  </v-btn>
		  <v-btn primary class='mt-3' icon='icon' v-else
		    @click.native='startPlaying'>
		    <v-icon>play_arrow</v-icon>
		  </v-btn>
		</v-col>
		<v-col xs10>
		  <v-slider v-bind:thumb-label='true' v-bind:min='0' 
		    v-bind:max='maxDuration()' v-bind:step='2'
		    @click.native='adjustSlider'
		    append-icon='timelapse' v-model='currentTime'></v-slider>
		</v-col>
	      </v-row>
	    </v-container>
	  </v-card-text>
	  </v-card-row>
	</v-card>
	</v-col>

	<v-col xs8>
	  <v-card id='data-1' v-for='channel in currentSession.channels'
	      key='channel.physicalChannel'>
	    <v-card-title class='blue-grey darken-2 white--text'>
	      {{channel.description}}
	      <v-chip class="blue-grey lighten-1 black--text pa-3">
		<v-avatar class='black--text'>
		  <v-icon>query_builder</v-icon>
		</v-avatar>
		{{currentTime | sprintf('%03.2f')}} of 
		{{channelDuration(channel.physicalChannel) | sprintf('%.1f')}} 
		seconds
	      </v-chip>
	      <v-chip class="blue-grey lighten-1 black--text pa-3">
		<v-avatar class='black--text'>
		  <v-icon>timeline</v-icon>
		</v-avatar>
		{{channelSamplingRate(channel.physicalChannel) | 
		sprintf('%.1f')}} Hz
	      </v-chip>
	      <v-spacer/>
		<v-btn 
		  v-tooltip:left="{ html: 'ANNOTATE TIME SERIES' }"
		  icon='icon'>
		  <v-icon>
		    insert_comment
		  </v-icon>
		</v-btn>
	    </v-card-title>
	    <v-card-row>
	      <smooth-chart
		:channel='channel.physicalChannel' 
		:recording='streaming'
		:data='channelData(channel.physicalChannel)'
		:reset-time='minChartTime'>
	      </smooth-chart>
	    </v-card-row>
	  </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  
  import SmoothChart from './SmoothChart'

  export default {
    
    props: ['id'],

    components: {SmoothChart},

    data() {
      return {
	currentTime: 0,
	minTime: 0,
	dataInterval: null,
	latestTimestamp: 0,
	recording: false,
	streaming: false,
	minChartTime: 0
      }	
    },

    methods: {
      adjustSlider() {
	this.minChartTime = this.currentTime
	this.$store.dispatch('updateStream', 
	  {id: this.id, minTime: this.currentTime, maxTime:-1})
      },
      startRecording() {
	  var data = {id: this.id, cmd: "start"}
	  this.$store.dispatch('sessionCommand', data)
	  this.recording = true
	  this.streaming = true

	  // Grab new data from the server every second.
	  this.dataInterval = setInterval(this.getNewData, 1000)
      },
      stopRecording() {
	  var data = {id: this.id, cmd: "stop"}
	  this.$store.dispatch('sessionCommand', data)
	  clearInterval(this.dataInterval)
	  this.dataInterval = null
	  this.recording=false
	  this.streaming = false
      },
      startPlaying() {
	// Grab new data from the server every second. But do not record new
	// data.
	this.dataInterval = setInterval(this.getNextData, 2000)
	this.streaming = true
      },
      stopPlaying() {
	// Stop playing; TODO: Change 'recording' to 'streaming'.
	clearInterval(this.dataInterval)
	this.streaming=false
      },
      getNextData() {
	this.currentTime = this.maxTime()
	var params = {id: this.id, minTime: this.currentTime, maxTime:-1}
	this.$store.dispatch('updateStream', params)
      },
      getNewData() {
	this.$store.dispatch('updateStream', 
	  {id: this.id, minTime: -1, maxTime:-1})
      },
      channelDuration(channelRequest) {
	var data = this.$store.state.currentData
	for (var k=0; k<data.length; k++) {
	  if (data[k].physicalChannel == channelRequest) {
	    return data[k].duration
	  }
	  else {
	    return 0
	  }
	}
      },
      channelSamplingRate(channelRequest) {
	var data = this.$store.state.currentData
	for (var k=0; k<data.length; k++) {
	  if (data[k].physicalChannel == channelRequest) {
	    return data[k].samplingRate
	  }
	  else {
	    return 0
	  }
	}
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
      maxTime() {
	var maxT = -1
	var data = this.$store.state.currentData
	for (var k=0; k<data.length; k++) {
	  if (data[k].maxTime>maxT)
	    maxT = data[k].maxTime
	}
	if (maxT < 0) {
	  this.stopPlaying()	
	}
	return maxT
      },
      maxDuration() {
	var data = this.$store.state.currentData
	if (data.length > 0) {
	  return data[0].duration	
	} else {
	  return 100	
	}
      }
    },

    computed: {
      currentSession() {
	return this.$store.state.currentSession
      }
    },

    mounted() {
      // Load the current session.
      this.$store.dispatch('getSession', this.id)

      // Prime it with some data, if possible.
      var params = {id: this.id, minTime: 0, maxTime:2 }
      this.$store.dispatch('updateStream', params)
    }
  
  }

</script>

<style>
  
</style>

