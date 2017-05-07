<template>
  <v-container fluid class='ma-3'>

    <v-row>
      
      <v-col xs3>

	<v-card>
	  <v-card-title class='blue-grey darken-4 white--text'>
	    {{currentSession.name}}
	    <v-spacer/>
	      <v-chip class="blue-grey darken-4 white--text">
		<v-avatar class='white--text pl-4'>
		  <v-icon>equalizer</v-icon>
		</v-avatar>
	      </v-chip>
	    </v-card-title>

	  <v-card-row class='blue-grey darken-4'>
	  <v-card-text>
	    <v-card-row>
	      <v-slider v-bind:thumb-label='true' v-bind:min='0' 
	       v-bind:max='maxDuration()' v-bind:step='0'
	       class='white--text shift-up' dark
	       @click.native='adjustSlider'
	       append-icon='timelapse' v-model='sliderPosition'></v-slider>
	    </v-card-row>

	    <v-card-row actions class='shift-up'>
	      <annotation-modal v-bind:id='id'></annotation-modal>
	      <v-btn primary class='mr-2' icon='icon' v-if='playback'
	       v-tooltip:top="{ html: 'Pause playback' }"
	       @click.native='stopPlaying'>
		<v-icon>pause</v-icon>
	      </v-btn>
	      <v-btn primary class='mr-2' icon='icon' v-else
	       v-tooltip:top="{ html: 'Playback data' }"
	       :disabled='recording'
	       @click.native='startPlaying'>
		<v-icon>play_arrow</v-icon>
	      </v-btn>
	      <v-btn icon='icon' class='mr-2' error v-if='recording'
	       v-tooltip:top="{ html: 'Pause Data Recording' }"
	       @click.native='stopRecording'>
		<v-icon error>pause</v-icon>
	      </v-btn>
	      <v-btn icon='icon' class='mr-2' error 
	       v-tooltip:top="{ html: 'Record Data' }"
	       :disabled='playback'
	       v-else @click.native='startRecording'>
		<v-icon error>fiber_manual_record</v-icon>
	      </v-btn>
	    </v-card-row>

	  </v-card-text>
	  </v-card-row>
	  </v-card>
	</v-col>

	<v-col xs9>
	  <v-card id='data-1' v-for='channel in currentSession.channels'
	      key='channel.physicalChannel'>
	    <v-card-title class='blue-grey lighten-2 white--text'>
	      {{channel.description}}
	      <v-chip class="blue-grey lighten-1 white--text pa-3">
		<v-avatar class='white--text'>
		  <v-icon>query_builder</v-icon>
		</v-avatar>
		{{elapsedTime | sprintf('%03.1f')}} of 
		{{channelDuration(channel.physicalChannel) | sprintf('%.1f')}} 
		seconds
	      </v-chip>
	      <v-chip class="blue-grey lighten-1 white--text pa-3">
		<v-avatar class='white--text'>
		  <v-icon>timeline</v-icon>
		</v-avatar>
		{{channelSamplingRate(channel.physicalChannel) | 
		sprintf('%.1f')}} Hz
	      </v-chip>
	      <v-spacer/>
	    </v-card-title>
	    <v-card-row class='ma-4'>

	      <data-chart 
		:data='channelData(channel.physicalChannel)'
	        :reset-buffer='resetBuffer'
		:play='streaming'>
	      </data-chart>

	    </v-card-row>
	  </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script>
  
  import DataChart from './DataChart'
  import AnnotationModal from './AnnotationModal'

  export default {
    
    props: ['id'],

    components: {DataChart, AnnotationModal},

    data() {
      return {
	annotate: false,
	resetBuffer: false,
	currentTime: 0,
	minTime: 0,
	dataInterval: null,
	latestTimestamp: 0,
	recording: false,
	streaming: false,
	playback: false,
	minChartTime: 0,
	sliderPosition: 0
      }	
    },

    watch: {
      elapsedTime: function() {
	this.sliderPosition = this.$store.state.elapsedTime
      } 
    },

    methods: {
      adjustSlider() {
	this.resetBuffer = !this.resetBuffer
	this.streaming = false
	this.playback = false
	this.recording= false
	this.$store.commit('setTime', this.sliderPosition)
	this.minChartTime = this.sliderPosition
	clearInterval(this.dataInterval)
	this.$store.dispatch('updateStream', 
	  {id: this.id, minTime: this.minChartTime, maxTime:0})
      },
      startRecording() {
	  this.$store.commit('setTime', this.maxDuration())
	  this.resetBuffer = !this.resetBuffer
	  var data = {id: this.id, cmd: "start"}
	  this.$store.dispatch('sessionCommand', data)
	  this.recording = true
	  this.streaming = true
	  this.playback = false

	  // Grab new data from the server every second.
	  this.getNewData()
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
	this.streaming = true
	this.recording = false
	this.playback = true
	this.dataInterval = setInterval(this.getNextData, 1000)
	this.getNextData()
      },
      stopPlaying() {
	// Stop playing; TODO: Change 'recording' to 'streaming'.
	clearInterval(this.dataInterval)
	this.minChartTime = this.currentTime 
	this.streaming=false
	this.playback = false
	this.recording = false
      },
      getNextData() {
	this.currentTime = this.maxTime()
	var params = {id: this.id, minTime: this.currentTime, maxTime:0}
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
      maxDuration() {
	var data = this.$store.state.currentData
	var maxDuration = 0
	for (var k=0; k<data.length; k++) {
	  if (data[k].duration > maxDuration) {
	    maxDuration = data[k].duration 
	  }
	}
	return maxDuration
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
	console.log('New Data Packaged!')
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
	  // No more data available; stop requesting data from the server.
	  console.log('Server has no more data :/')
	  clearInterval(this.dataInterval)
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
      },
      elapsedTime() {
	var elapsed =  this.$store.state.elapsedTime 
	return elapsed
      }
    },

    mounted() {

      // Load the current session.
      this.$store.dispatch('getSession', this.id)

      // Reset the elapsed time.
      this.$store.commit('setTime', 0.0)

      // Prime it with some data, if possible.
      var params = {id: this.id, minTime: 0, maxTime:0}
      this.$store.dispatch('updateStream', params)
    }
  
  }

</script>

<style>

  .shift-up {
    margin-top: -25px; 
  }
  
</style>

