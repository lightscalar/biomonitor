<template>
  <v-container fluid class='ma-3'>
    
    <v-row>

      <v-col xs4>
	<v-card>
	  <v-card-row>
          <v-card-title class='blue-grey darken-4 white--text'>
	      Create a New Session
	    </v-card-title>
	  </v-card-row>
	  <v-card-row class='blue-grey darken-4'>
	    <v-card-text>
	      <v-text-field class='black--text'
		 v-model = 'sessionName'
		 dark
		 name="input-1"
		 label="Session Name">
	      </v-text-field>
	    </v-card-text>
	  </v-card-row>

	  <v-card-row class='blue-grey darken-4'>
	    <v-container class="">
	      <v-row v-for='(item, index) in currentChannels' :key='item.id'>
		<v-col xs5>
		  <v-text-field v-model="item.description" dark
		  label="Channel Description">
		  </v-text-field>
		</v-col>
		<v-col xs5>
		  <v-text-field v-model="item.physicalChannel" dark
		  label="Physical Channel">
		  </v-text-field>
		</v-col>
		<v-col xs2 v-if='currentChannels.length>1'>
		  <v-btn floating small error
			@click.native='deleteChannel(index)'>
		    <v-icon>
		      delete
		    </v-icon>
		  </v-btn>
		</v-col>
	      </v-row>
	    </v-container>

	  </v-card-row>
	  <v-card-row action class='blue-grey darken-4'>
	    <v-spacer/>
	    <v-btn default light @click.native='addChannel()' dark>
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

      <v-col xs8>
	<v-card width='100%'>
	  <v-card-row>
	    <v-card-title class='blue-grey lighten-2 white--text'>
	       Session Archive
	      </v-card-title>
	    </v-card-row>

	    <v-card-row class='pa-4'>
	      <v-pagination circle v-bind:length.number="pages.length" 
		v-model="currentPage"/>
	    </v-card-row>

	    <v-card-row class='pa-3'>

	      <v-data-table v-if='sessionList.length>0' 
		v-bind:headers='tableHeaders'
		v-model='sessionList'
		hide-actions>
	        <template slot='items' scope='props'>
		  <td>
		    <router-link 
		      :to="{name: 'session', params:{id: props.item._id}}">
		      {{props.item.name}}
		    </router-link>
		  </td>
		  <td>{{props.item._id}}</td>
		  <td>{{props.item.createdAt}}</td>
		  <td>
		    <v-btn icon='icon' dark small class='grey lighten-1'
		      @click.native='deleteSession(props.item._id)'>
		      <v-icon>delete</v-icon>
		    </v-btn>
		  </td>
		</template>
	      </v-data-table>
	      <h6 class='ma-5' v-else>
		No sessions are currently in the database. Add one using the
		form to the left.
	      </h6>
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
	tableHeaders: [{text:'Session Name', left: true, value:'name'},
		       {text:'Session ID', left: true, value:'_id'},
		       {text:'Created At', left: true, value:'createdAt'}],
	currentPage: 1,
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
	  this.currentChannels.push({description: null,
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
      },
      deleteSession(id) {
	this.$store.dispatch('deleteSession', id)
      }
    },

    computed: {
      defaultChannels() {
	return this.$store.state.defaultChannels 
      },
      pages() {
	return utils.chunkArray(this.$store.state.sessionList,5) 
      },
      sessionList() {
	if (this.pages.length>0) {
	  return this.pages[this.currentPage-1]
	} else {
	  return []
	}
      },
    },

    mounted() {
      this.currentChannels = this.$store.state.defaultChannels
      this.$store.dispatch('listSessions')
    }

  }

</script>


<style>

</style>

