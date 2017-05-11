import Vue from 'vue'
import Vuex from 'vuex'
import api from '../api/connect'
Vue.use(Vuex)

var defaultStatus = {isConnected: false,
		     statusMessage: 'Cannot find webserver.',
		     devicePort: 'UNAVAILABLE'}
var defaultChannels = [{description: 'PVDF Sensor',
			physicalChannel: 1, id:0}]
var currentSession = {}
var sessionList = []

export default new Vuex.Store({

  // ------ STATE VARIABLES --------------------
  state: {
    deviceStatus: defaultStatus,
    defaultChannels: defaultChannels,
    currentSession: currentSession,
    sessionList: sessionList,
    currentData: [],
    dataHistory: [],
    elapsedTime: 0,
    bpm: {0:[], 1:[], 2:[]},
    metric: {0:[], 1:[], 2:[]}
  },

  // -------- GETTERS --------------------------
  getters: {
    maxTime: state => {
      if (state.currentData.length>0) {
	var len = state.currentData[0].data.length
	if (len>0) {
	  return state.currentData[0].data[len-1][0]
	}
      }
      return 0
    }
  },

  // ------ MUTATIONS ------------------------
  mutations: {
    setStatus(state, newDeviceStatus) {
      state.deviceStatus = newDeviceStatus 
    },
    attachDevice(state, devicePort) {
      state.devicePort = devicePort
    },
    setCurrentSession(state, data) {
      state.currentSession = data 
    },
    setSessionList(state, data) {
      state.sessionList = data
    },
    resetReportables(state, data) {
      state.bpm = {0:[], 1:[], 2:[]},
      state.metric = {0:[], 1:[], 2:[]}
    },
    setCurrentData(state, data) {
      state.currentData = data

      // Update reportable parameters.
      var nChan = data.length
      for (var k=0; k<nChan; k++) {
	var physChan = data[k].physicalChannel
	var datum = data[k]
	var timestamp = (datum.maxTime + datum.minTime)/2
	state.bpm[physChan].push({t: timestamp, bpm: datum.bpm})
	state.metric[physChan].push({t: timestamp, metric: datum.metric})
      }
    },
    setDataHistory(state, data) {
      state.dataHistory = data 
    },
    setTime(state, data) {
      state.elapsedTime = data
    },
  },

  // ------ ACTIONS ------------------------
  actions: {
    checkStatus(context) {
      // Check biomonitor status.
      api.getStatic('status').then(function(resp) {
	context.commit('setStatus', resp.data)
      }).catch(function() {
        context.commit('setStatus', defaultStatus)
      })
    },
    createSession(context, data) {
      // Create a new session.
      api.postResource('sessions', data).then(function(resp) {
	context.commit('setCurrentSession', resp.data)
	router.push({name: 'session', params: {id: resp.data._id}})
      }) 
    },
    createAnnotation(context, data) {
      // Create a new annotation; update list of annotations.
      var owner_id = data.owner_id
      api.postResource('annotations', data).then(function(resp) {
	context.dispatch('getSession', owner_id)
      }) 
    },
    getSession(context, id) {
      // Get a specified session.
      api.getResource('session', id).then(function(resp) {
	context.commit('setCurrentSession', resp.data)
	context.commit('resetReportables', resp.data)
      })
    },
    listSessions(context) {
      // List all sessions in database.
      api.listResource('sessions').then(function(resp) {
	context.commit('setSessionList', resp.data)
      })
    },
    deleteSession(context, id) {
      // Delete the session at /id.
      api.deleteResource('session', id).then(function(resp) {
	context.dispatch('listSessions')
      }) 
    },
    deleteAnnotation(context, id) {
      // Delete the session at /id.
      api.deleteResource('annotation', id).then(function(resp) {
	console.log('Deleted the session.')
      }) 
    },
    sessionCommand(context, data) {
      // Send a command (data.cmd) to the specified session (data.id).
      api.putResource('session', data).then(function(resp) {
      }).catch(function() {
	console.log('OOPS!')
      })
    },
    getHistory(context, data) {
      api.getHistory('session', data).then(function(resp) {
	context.commit('setDataHistory', resp.data)
      })
    },
    updateStream(context, data) {
      api.streamResource('session', data).then(function(resp) {
	context.commit('setCurrentData', resp.data)
      })
    }
  }
})
