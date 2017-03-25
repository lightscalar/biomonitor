<template>
  <v-container>
    <v-row class='mt-5'>
      <v-col xs2 class="">
      </v-col>

      <v-col xs8 class="">
	<v-card>
	  <v-card-row>
	    <v-card-title class='black white--text'>
	      Create New Data Session
	    </v-card-title>
	  </v-card-row>
	  <v-card-row>
	    <v-card-text>
	      <v-text-field
		 v-model = 'sessionName'
		 name="input-1"
		 label="Session Name">
	      </v-text-field>
	    </v-card-text>
	  </v-card-row>

	  <v-card-row>

	    <v-container class="">
	      <v-row v-for='(item, index) in currentChannels' :key='item.id'>
		<v-col xs5>
		  <v-text-field v-model="item.channelDescription" 
		  label="Channel Description">
		  </v-text-field>
		</v-col>
		<v-col xs5>
		  <v-text-field v-model="item.physicalChannel" 
		  label="Physical Channel">
		  </v-text-field>
		</v-col>
		<v-col xs2 v-if='currentChannels.length>1'>
		  <v-btn error floating small dark
		    @click.native='deleteChannel(index)'>
		    <v-icon >
		      delete
		    </v-icon>
		  </v-btn>
		</v-col>
	      </v-row>

	    </v-container>
	  </v-card-row>
	  <v-card-row action>
	    <v-btn default light @click.native='addChannel()'>
	      <v-icon class='mr-1' >
		note_add
	      </v-icon> 
	      Add Channel</v-btn>
	    <v-btn primary @click.native='createSession'>
	      <v-icon class='mr-1'>trending_up</v-icon> 
	      Create Session
	    </v-btn>
	  </v-card-row>
	</v-card>
      </v-col>
    </v-row>
    
      <v-snackbar v-model='showMessage' top>
	{{errorMessage}}
	<v-btn flat class="pink--text" @click.native="showMessage=false">
	  Close
	</v-btn>
      </v-snackbar>

  </v-container>
</template>

<script>
  
  // import Component from "../component_location"

  export default {
    
    components: {},

    data() {
      return {
	sessionName: null,
	channel: null,
	currentChannels: [],
	showMessage: false,
	errorMessage: ''
      }	
    },

    methods: {
      deleteChannel(index) {
	if (this.currentChannels.length > 1) {
	  this.currentChannels.splice(index,1)
	}
      },

      addChannel() {
	if (this.currentChannels.length<2) {
	  this.currentChannels.push({channelDescription: null,
	    physicalChannel: null, id: this.currentChannels.length}) 
	}
      },

      createSession() {
	if (!this.sessionName) {
	  this.errorMessage = 'The session must have a name.'
	  this.showMessage = true	
	} else {
	  var sessionData = {name: this.sessionName, channels: 
	    this.currentChannels}
	  this.$store.dispatch('createSession', sessionData)
	}
      }
    },

    computed: {
      defaultChannels() {
	return this.$store.state.defaultChannels 
      } 
    
    },

    mounted() {
      this.currentChannels = this.$store.state.defaultChannels
    }
  
  }

</script>


<style>
  
</style>

