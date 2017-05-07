<template>
  <div style='display: block; width: 100%'>
    <div id='channel-1' class='chart' width='800' height='200'></div>
  </div>
</template>

<script>

// import Component from "../component_location"

  export default {

    components: {},

    props: ['channel', 'data', 'play', 'resetBuffer'],

    data() {
      return {
	stream: false,
	buffer: [],
	doReset: false,
	chart: null,
	chartData:[],
	interval: [],
	numberChartPoints:300
      }	
    },

    computed: {

    },

    watch: {
      data: function() {
	// If we've changed something, clear chart data.
	if (this.doReset) {
	  this.buffer = []	
	  while (this.chartData.length>0) {
	    this.chartData.shift() 
	  }
	  this.chart.render()
	  this.doReset = false // until user intervenes again
	}
	// If data is new to us, add it to the buffer.
	if (this.dataMin() >= this.bufferMax()) {
	  this.buffer = this.buffer.concat(this.data)  
	} else {
	  console.log('No new data!')
	}
	// If nothing in chart, display everything we can.
	if ((this.chartData.length == 0) && (this.buffer.length>0)) {
	  this.fillChartData() // fill that chart up
	}
      },
      play: function() {
	if (this.play) {
	  console.log('Starting to stream data.')
	  this.stream = true
	  this.pushData()	
	} else {
	  this.stream = false
	} 
      },
      resetBuffer: function() {
	this.doReset = true
	console.log('Resetting the buffer.')
      }
    },

    methods: {
      fillChartData() {
	var numPoints = Math.min(this.buffer.length, this.numberChartPoints)
	for (var k=0; k<numPoints; k++) {
	  var datum = this.buffer.shift()
	  datum = {x: datum[0], y: datum[1]}
	  this.chartData.push(datum)
	}
	this.chart.render()
      },
      pushData() {
	var datum = null
	if (this.stream) { // stream this data to the chart.
	  var dt = 25 // milliseconds between updates.
	  var maxPts = Math.min(6, this.buffer.length)
	  for (var itr=0; itr<maxPts; itr++) {
	    datum = this.buffer.shift()
	    datum = {x: datum[0], y: datum[1]}
	    if (datum.x > this.chartMax()) {
	      // We haven't seen this data yet, so add it.
	      console.log('Pushing data.')
	      this.chartData.push(datum)
	    } else {
	      console.log('Cannot push buffer data into chart.')
	    }
	  }
	  if (datum) {
	    // Update the current elapsed time.
	    this.$store.commit('setTime', datum.x)
	  }
	  if (this.chartData.length>this.numberChartPoints) {
	    while (this.chartData.length>this.numberChartPoints) {
	      this.chartData.shift()	
	    }
	  }
	  if (this.stream) {
	    // Grab the next data!
	    if (dt>0) {
	      setTimeout(this.pushData, dt)
	    }
 	  }
	  console.log('Rendering chart!')
	  this.chart.render()
	}
      },
      chartMax() {
	var maxTime = 0
	for (var k=0; k<this.chartData.length; k++) {
	  if (this.chartData[k].x > maxTime) {
	    maxTime = this.chartData[k].x
	  }
	}
	return maxTime
      },
      bufferMax() {
	var maxTime = 0
	for (var k=0; k<this.buffer.length; k++) {
	  if (this.buffer[k][0] > maxTime) {
	    maxTime = this.buffer[k][0] 
	  }
	}
	return maxTime
      },
      dataMin() {
	var minTime = Number.POSITIVE_INFINITY
	for (var k=0; k<this.data.length; k++) {
	  if (this.data[k][0] < minTime) {
	    minTime = this.data[k][0] 
	  }
	}
	return minTime
      }
    },

    mounted() {
      this.chart = new CanvasJS.Chart('channel-1', {
	theme: 'theme1' ,
	axisX: {
	  gridColor: 'lightGray',
	  gridThickness: 1,
	  title: 'Elapsed Time (seconds)',
	  titleFontFamily: 'Avenir Next',
	  titleFontSize: 14,
	  labelFontSize: 14,
	  interval: 0.50,
	  intervalType: 'seconds'
	},
	axisY: {
	  title: 'Amplitude (voltage)',
	  titleFontFamily: 'Avenir Next',
	  gridThickness: 1,
	  titleFontSize: 14,
	  labelFontSize: 14
	},
	data: [
	  {
	    type: "spline",
	    lineColor: '#3C78CD',
	    dataPoints: this.chartData
	  }]
      })
      this.chart.render()
    }

  }

</script>

<style>
  .chart {
    min-height: 300px;
    display: block;
  }
</style>

