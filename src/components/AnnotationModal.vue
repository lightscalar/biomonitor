<template>
<v-dialog v-model='modalState' 
  fullscreen transition="v-dialog-bottom-transition">
  <v-btn slot='activator' class='white--text slide-left'
    v-tooltip:top="{ html: 'ANNOTATE SESSION' }" flat primary>
    <v-icon large>
      insert_comment
    </v-icon>
  </v-btn>

  <v-toolbar class='elevation-0 blue-grey darken-4'>
    <v-btn @click.native="modalState=false" error floating medium>
      <v-icon>close</v-icon>
    </v-btn>
    <v-toolbar-title>
      Manage Annotations for {{currentSession.name}}
    </v-toolbar-title>
  </v-toolbar>

  <v-container fluid class='ma-3'>

    <v-row>
      <v-col xs3>
	<v-card class='blue-grey darken-4'>
	  <v-card-title class='blue-grey darken-4 white--text'>
	    New ({{elapsedTime | sprintf('%0.1f')}} seconds)
	  </v-card-title>
	  <v-card-text class='blue-grey darken-4'>
	    <v-text-field
	      dark
	     class='pa-2'
	     style='border: 1px solid #3b4348'
	      label="Annotation Text" 
	      v-model='annotationText'
	      multi-line>
	    </v-text-field>
	  </v-card-text>
	  <v-card-row actions class='dark-grey darken-4'>
	    <v-btn dark primary @click.native='saveAnnotation'>
	      Add Annotation
	    </v-btn>
	  </v-card-row>
	</v-card>
      </v-col>

      <v-col xs9>
	<v-card>
	  <v-card-title class='blue-grey lighten-2 white--text'>
	    Current Annotations
	  </v-card-title>
	  <v-card-row class='pa-3'>
	    <v-data-table
		 rows-per-page-text='4'
		 v-bind:headers='tableHeaders'
		 v-model='currentSession.annotations'
		 hide-actions>
	       <template slot='items' scope='props'>
		<td>{{props.item.createdAt}}</td>
		<td>{{props.item.elapsedTime | sprintf('%.2f')}}</td>
		<td>{{props.item.text}}</td>
		<td>
		  <v-btn icon='icon' dark small class='grey lighten-1'
		    @click.native='deleteAnnotation(props.item._id)'>
		    <v-icon>delete</v-icon>
		  </v-btn>
		</td>
	      </template>
	    </v-data-table>
	  </v-card-row>
	</v-card>
      </v-col>
    </v-row>
  </v-container>

</v-dialog>

</template>

<script>
  
  // import Component from "../component_location"

  export default {
    
    props: ['id'],

    components: {},

    data() {
      return {
	modalState: false,
	annotationText: '',
	tableHeaders: [{text:'Timestamp', left:true, value:'createdAt'},
		       {text:'Elapsed Time', left:true, 
			 value:'elapsedTime'},
		       {text:'Event Description', left:true, value:'text'}]
      }	
    },

    computed: {
      elapsedTime() {
	return this.$store.state.elapsedTime 
      },
      annotations() {
	return this.$store.state.currentAnnotations 
      },
      currentSession() {
	return this.$store.state.currentSession 
      }
    },

    methods: {

      saveAnnotation() {
	// Save the annotation to the database.
	var annotation = {}
	annotation.text = this.annotationText
	annotation.owner_id = this.currentSession._id
	annotation.elapsedTime = this.$store.state.elapsedTime
	annotation.createdAtEpoch = Date.now()
	annotation.createdAt = Date()
	this.$store.dispatch('createAnnotation', annotation)
	this.annotationText = ''
      },

      deleteAnnotation(_id) {
	// Delete the specified annotation from the server.
	console.log('Deleting that guy: ' + _id)
	this.$store.dispatch('deleteAnnotation', _id)
	// Now remove it locally.
	for (var k=0; k<this.currentSession.annotations.length; k++) {
	  if (this.currentSession.annotations[k]._id == _id ) {
	    this.currentSession.annotations.splice(k,1)
	  }
	}
      }
    },

    mounted() {

      console.log(this.id)
      this.$store.dispatch('getSession', this.id)
    }
  
  }

</script>


<style>
  .slide-left {
    margin-right: -20px !important;
    margin-top: -12px !important;
  }  
</style>

