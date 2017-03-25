import Vue from 'vue'
import Vuex from 'vuex'
import api from '../api/connect'
Vue.use(Vuex)

var defaultStatus = {isConnected: false,
		   statusMessage: 'Checking for devices.',
		   availableDevices: []}
var defaultChannels = [
  // {channelDescription: 'PPG Sensor', physicalChannel: 0},
  {channelDescription: 'PVDF Sensor', physicalChannel: 1, id:0}
]
var currentSession = {}
var sessionList = []

export default new Vuex.Store({

  state: {
    deviceStatus: defaultStatus,
    devicePort: null,
    defaultChannels: defaultChannels,
    currentSession: currentSession,
    sessionList: sessionList
  },

  mutations: {
    setStatus(state, newDeviceStatus) {
      state.deviceStatus = newDeviceStatus 
    },
    attachDevice(state, devicePort) {
      state.devicePort = devicePort
    },
    setCurrentSession(state, data) {
      state.currentSession = data 
    }
  },

  actions: {
    checkStatus(context) {
      api.getStatic('status').then(function(resp) {
	context.commit('setStatus', resp.data)
	if (context.state.deviceStatus.availableDevices.length == 1) {
	  var selectedDevice = context.state.deviceStatus.availableDevices[0]
	  context.commit('attachDevice', selectedDevice)
	}
	if (!context.state.deviceStatus.isConnected) {
	  router.push({path: '/'})
	}
      }).catch(function() {
        context.commit('setStatus', defaultStatus)
      })
    },

    createSession(context, data) {
      api.postResource('sessions', data).then(function(resp) {
	context.commit('setCurrentSession', resp.data)
	router.push({name: 'session', params: {id: resp.data._id}})
      }) 
    },

    getSession(context, id) {
      api.getResource('session', id).then(function(resp) {
	context.commit('setCurrentSession', resp.data)
      })
    },

    startCollection(context) {
      var command = {
	command: 'COLLECT', 
	sessionId: context.state.currentSession._id
      }
      api.postResource('command', command).then(function(resp) {
	// context.commit('deviceStatus', 'COLLECTING')
      }).catch(function(){
	// context.commit('deviceStatus', 'IDLE')   
      })
    },
    stopCollection(context) {
      var command = {
	command: 'IDLE', 
	sessionId: context.state.currentSession._id
      }
      api.postResource('command', command).then(function(resp) {
	// context.commit('deviceStatus', 'COLLECTING')
      }).catch(function(){
	// context.commit('deviceStatus', 'IDLE')   
      })
    }
  }
   

})
