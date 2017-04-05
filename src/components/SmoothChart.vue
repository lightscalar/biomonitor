<template>
  <div class='ma-3'>
    <canvas id='channel-1' class='chart' width='800' height='400'></canvas>
  </div>
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
	  console.log('Adding data')
	  this.maxTime = maxDataTime
	  this.buffer = this.buffer.concat(this.data)
	}
      },
      reset: function() {
	if (this.reset) {
	  console.log('Collecting')
	  this.updatingChart = true
	  this.pushData()
	} else {
	  console.log('Stopping Collection')
	  this.updatingChart = false
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
      // options.minValue = 0.05
      // options.maxValue = 0.11
      options.millisPerPixel = 5
      options.scaleSmoothing = 0.5
      options.grid = {}
      options.grid.millisPerLine = 1000
      options.grid.sharpLines = true
      options.grid.fillStyle= '#cccccc'

      var smooth = new SmoothieChart(options)
      smooth.streamTo(document.getElementById('channel-1'), 1000)
      this.timeSeries = new TimeSeries()
      smooth.addTimeSeries(this.timeSeries,
	{lineWidth:2,strokeStyle:'#0080ff',fillStyle:'rgba(102,204,255,0.30)'})
    }

  }

</script>


<style>
  .chart {
    display: block;
  }
</style>

