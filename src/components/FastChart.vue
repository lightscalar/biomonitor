<template>
  <div class='ma-3'>
    <div id='channel-1' class='chart' width='400' height='200'></div>
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
	maxTime: 0,
	minTime:-1,
	chartData:[],
	buffer: [],
	interval:[]
      }	
    },

    computed: {

    },

    watch: {
      data: function() {
	
	// Buffer up some of this good data.
	var len = this.buffer.length
	if (len>0 && this.data.length>0) {
	  if (this.data[0][0] > this.buffer[len-1][0]) {
	    this.buffer = this.buffer.concat(this.data)
	  }
	}
	this.buffer = this.buffer.concat(this.data)
      },
      reset: function() {
	if (this.reset) {
	  console.log('Setting interval')
	  this.interval = setInterval(this.updateChart, 250)
	} else {
	  console.log('Clearing interval!')
	  clearInterval(this.interval)
	}
      }
    },

    methods: {
      updateChart() {
	console.log(this.chartData.length)
	if (this.chartData.length>1500) {
	  for (var k=0; k<(this.chartData.length-1500); k++) {
	    this.chartData.shift() 
	  }
	}
	var bufLen= this.buffer.length
	if (bufLen>250) {
	  for (var k=0; k<bufLen; k++) {
	    if (k==0) {
	      var startTime = this.buffer[k][0] 
	    }
	    var ts = this.buffer[k][0]
	    var vl = this.buffer[k][1]
	    if (ts>this.maxTime) {
	      this.maxTime = ts
	      this.chartData.push({x: ts, y: vl})
	      if (this.chartData.length>1500) {
		this.chartData.shift()
	      }
	    }
	  }
	  this.buffer = []
	}
	this.chart.render()
      }
    },

    mounted() {
      this.chart = new CanvasJS.Chart('channel-1', {
	theme: 'theme1' ,
	axisX: {
	  gridColor: 'lightGray',
	  gridThickness: 0,
	  title: 'Time (seconds)',
	  titleFontFamily: 'Avenir Next',
	  titleFontSize: 14,
	  labelFontSize: 14,
	  interval: 0.25,
	  intervalType: 'seconds'
	},
	axisY: {
	  title: 'Amplitude (voltage)',
	  titleFontFamily: 'Avenir Next',
	  titleFontSize: 14,
	  labelFontSize: 14
	},
	data: [
	  {
	    type: "line",
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

