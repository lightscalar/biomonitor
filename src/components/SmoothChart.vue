<template>
  <canvas id='channel-1' width='500' height='200'></canvas>
</template>

<script>

// import Component from "../component_location"

  export default {

    components: {},

    props: ['channel', 'data', 'recording', 'resetTime'],

    data() {
      return {
	chart: null,
	counter: 0,
	maxTime: 0,
	minTime:-1,
	chartData:[],
	buffer: [],
	interval:[],
	timeSeries:[],
	updatingChart: false
      }	
    },

    computed: {
    },

    watch: {
      resetTime: function() {
	console.log('Clearing the buffer!')
	this.buffer = []
	this.maxTime = 0
      },
      data: function() {
	// Buffer the data, if it is new to us.
	var maxDataTime = this.maxDataTime()
	if (maxDataTime > this.maxTime) {
	  console.log('Receiving Data Package!')
	  this.maxTime = maxDataTime
	  this.buffer = this.buffer.concat(this.data)
	}
      },
      recording: function() {
	if (this.recording) {
	  console.log('Collecting')
	  this.updatingChart = true
	  this.pushData()
	  this.chart.start()
	} else {
	  console.log('Stopping Collection')
	  this.updatingChart = false
	  this.chart.stop()
	}
      }
    },

    methods: {
      maxDataTime() {
	var maxTime = 0
	for (var k=0; k<this.data.length; k++) {
	  if (this.data[k][0]>maxTime) {
	    maxTime = this.data[k][0]
	  }
	}
	return maxTime
      },
      pushData() {
	// Grab next data. Push it in with appropriate delay.
	// The delay is now fixed. It is always 20 ms.
	var dt = 20 // milliseconds
	if (this.updatingChart) {
	  if (this.buffer.length>0) {
	    var datum = this.buffer.shift()
	    this.$store.commit('setTime', datum[0])
	    this.updateChart(datum[1])
	    setTimeout(this.pushData, dt)
	  } else {
	    setTimeout(this.pushData, 25*dt) // wait longer if no data present
	  } 
	}
      },
      updateChart(value) {
	this.timeSeries.append(new Date().getTime(), value)
      }
    },

    mounted() {
      var options = {}
      options.width = 1267
      // options.minValue = 0.05
      // options.maxValue = 0.11
      options.millisPerPixel = 5
      options.scaleSmoothing = 0.5
      options.grid = {}
      options.grid.millisPerLine = 1000
      options.grid.sharpLines = true
      options.grid.strokeStyle = '#cfcfcf'
      options.grid.fillStyle= '#6b8ba4'
      options.labels = {}
      options.labels.fontSize = 14
      options.interpolation = 'bezier'

      // Set up a new chart; stream to target html element.
      // TODO: Use the ID prop to do this properly in the future.
      var smooth = new SmoothieChart(options)
      smooth.streamTo(document.getElementById('channel-1'), 1000)

      // Add a new time series object; configure it r'il nice.
      this.timeSeries = new TimeSeries()
      var seriesOptions = {}
      seriesOptions.lineWidth=1,
      seriesOptions.strokeStyle='#0080ff'
      seriesOptions.fillStyle='rgba(102,204,255,0.30)'
      smooth.addTimeSeries(this.timeSeries, seriesOptions)

      // Let's update the size of the graph if windows resize...
      var y = $('#data-1').width()
      $('#channel-1').attr('width', y)
      $( window ).resize(function() {
	var y = $('#data-1').width()
	$('#channel-1').attr('width',y)
      })
      this.chart = smooth
      this.chart.render()
      this.chart.stop()
    }
  }

</script>


<style>
  .chart {
    width: 100%
  }
</style>

