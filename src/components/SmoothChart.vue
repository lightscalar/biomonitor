<template>
  <canvas id='channel-1' width='500' height='200'></canvas>
</template>

<script>

// import Component from "../component_location"

  export default {

    components: {},

    props: ['channel', 'data', 'reset'],

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
      data: function() {
	
	// Buffer the data, it it is new to us.
	var maxDataTime = this.maxDataTime()
	if (maxDataTime > this.maxTime) {
	  console.log('Data package arrived.')
	  this.maxTime = maxDataTime
	  this.buffer = this.buffer.concat(this.data)
	}
      },
      reset: function() {
	if (this.reset) {
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
	if (this.updatingChart) {
	  if (this.buffer.length>0) {
	    var dt = (this.buffer[1] - this.buffer[0])
	    var val = 0
	    val += this.buffer.shift()[1]
	    val += this.buffer.shift()[1]
	    val += this.buffer.shift()[1]
	    val += this.buffer.shift()[1]
	    this.updateChart(val/4)
	    setTimeout(this.pushData, 5)
	  } else {
	    setTimeout(this.pushData, 500)
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

      // Set up a new chart; stream to target html element.
      // TODO: Use the ID prop to do this properly in the future.
      var smooth = new SmoothieChart(options)
      smooth.streamTo(document.getElementById('channel-1'), 1000)

      // Add a new time series object; configure it r'il nice.
      this.timeSeries = new TimeSeries()
      var seriesOptions = {}
      seriesOptions.lineWidth=2,
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

