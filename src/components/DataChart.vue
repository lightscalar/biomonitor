<template>
  <div id='myChart' class='chart'></div>
</template>

<script>
  
  // import Component from "../component_location"

  export default {
    
    props: ['data'],

    components: {},

    data() {
      return {
	charts: [],
      }
    },

    methods: {

    },
    watch: {
      data: function() {
	this.charts[0].render()
      }
      
    },

    mounted() {

      var self = this

      // Create the charts!
      this.charts.push(new CanvasJS.Chart("myChart", {
	theme: 'theme1',
	axisX: {
	  gridColor: 'lightGray',
	  gridThickness: 2,
	  title: 'Time (seconds)',
	  titleFontFamily: 'Roboto',
	  titleFontSize: 16
	},
	axisY: {
	  title: 'PVDF Sensor',
	  titleFontFamily: 'Roboto',
	  titleFontSize: 16
	  // minimum: -2.0,
	  // maximum: 2
	},
	data: [
	  {
	    type: "line",
	    dataPoints: self.data

	  }]
      }))

      self.charts[0].render()

    }

  }

  </script>


<style>
  .chart {
    height: 300px;
  }
</style>

