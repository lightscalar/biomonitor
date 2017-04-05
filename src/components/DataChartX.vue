<template>
  <div class='ma-3'>
    <div id='channel-1' class='chart' width='400' height='200'></div>
  </div>
</template>

<script>

// import Component from "../component_location"

  export default {

    components: {},

    props: ['channel', 'data'],

    data() {
      return {
	chart: null,
	maxTime: 0,
	minTime:-1,
	chartData:[]
      }	
    },

    computed: {

    },

    watch: {
      data: function() {
	var len = this.data.length
	if (len>0) {
	  for (var k=0; k<len; k++) {
	    var ts = this.data[k][0]
	    var val = this.data[k][1]
	    if (ts > this.maxTime) {
	      this.chartData.push({x: ts, y:val})
	      this.maxTime = ts
	    }
	    if (this.chartData.length>1500) {
	      this.chartData.shift()
	    }
	  }
	}
	this.chart.render()
      }
    },

    methods: {
    },

    mounted() {
      this.chart = new CanvasJS.Chart('channel-1', {
	theme: 'theme1' ,
	axisX: {
	  gridColor: 'lightGray',
	  gridThickness: 2,
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

