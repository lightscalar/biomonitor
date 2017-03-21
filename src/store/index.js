import Vue from 'vue'
import Vuex from 'vuex'
Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    deviceStatus: {isConnected: false,
		   statusMessage: 'Checking for connection',
		   availableDevices: []}
  },
  mutations: {
    setStatus(state, newDeviceStatus) {
      state.deviceStatus = newDeviceStatus 
    }
  }
})
