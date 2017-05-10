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
	numberChartPoints:300,
	minY : null,
	maxY : null,
	lastTime: Date.now(),
	maxPtsCandidate: 5
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
	// console.log('Resetting the buffer.')
      }
    },

    methods: {
      updateRange() {
	var L = this.chartData.length
	if (L>0) {
	  var mean = 0
	  var data = []
	  var datum = 0
	  for (var k=0; k<L; k++) {
	    datum = this.chartData[k].y
	    mean += datum
	    data.push(datum) 
	  }
	  mean /= L
	  var std = 0
	  for (var k=0; k<L; k++){ 
	    std += (data[k] - mean)**2
	  }
	  std /= L
	  std = Math.sqrt(std)
	}
	var factor = 4.0
	var alpha = 0.95 // inertial smoothing factor
	var newMax = mean + factor * std
	var newMin = mean - factor * std
	if (this.maxY) {
	  this.maxY = alpha * this.maxY + (1-alpha) * newMax
	  this.minY = alpha * this.minY + (1-alpha) * newMin
	} else {
	  this.maxY = newMax
	  this.minY = newMin
	}
	this.chart.options.axisY.maximum = this.maxY
	this.chart.options.axisY.minimum = this.minY
	this.chart.render()
      },
      fillChartData() {
	var numPoints = Math.min(this.buffer.length, this.numberChartPoints)
	for (var k=0; k<numPoints; k++) {
	  var datum = this.buffer.shift()
	  datum = {x: datum[0], y: datum[1]}
	  this.chartData.push(datum)
	}
	// this.chart.render()
	this.updateRange()
      },
      pushData() {
	var datum = null
	if (this.stream) { // stream this data to the chart.

	  // Ostensibly we wil have 50 milliseconds between data pushes, but
	  // due to the vagaries of the browser, this may occasionally be 
	  // faster or slower. We therefore scale the number of data points we
	  // push based on the actual time it took to return.
	  var dt = 50 // milliseconds between updates.
	  var deltaTime = Date.now() - this.lastTime
	  this.maxPtsCandidate = Math.round(deltaTime/50 * 5)
	  var maxPts = Math.min(this.maxPtsCandidate, this.buffer.length)

	  for (var itr=0; itr<maxPts; itr++) {
	    datum = this.buffer.shift()
	    datum = {x: datum[0], y: datum[1]}
	    if (datum.x > this.chartMax()) {
	      // We haven't seen this data yet, so add it.
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
	      this.lastTime = Date.now()
	      setTimeout(this.pushData, 50)
	    }
 	  }
	  // console.log('Rendering chart!')
	  // this.chart.render()
	  this.updateRange()
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
	  labelFontSize: 14,
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

