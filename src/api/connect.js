import axios from 'axios'

const BASE_URL = 'http://localhost:1492' 
// Basic API for talking to the backend.
export default {

    getStatic(resourceName){
      var url = BASE_URL + '/' + resourceName
      return axios.get(url)
    },

    getResource(resourceName, id) {
      var url = BASE_URL + '/' + resourceName + '/' + id
      return axios.get(url)
    },

    listResource(resourceName) {
      var url = BASE_URL + '/' + resourceName
      return axios.get(url)
    },

    deleteResource(resourceName, id) {
      var url = BASE_URL + '/' + resourceName + '/' + id
      return axios.delete(url)
    },

    postResource(resourceName, data) {
      var url = BASE_URL + '/' + resourceName
      return axios.post(url, data)
    },

    putResource(resourceName, data) {
      var url = BASE_URL + '/' + resourceName + '/' + data.id
      return axios.put(url, data)
    },

    streamResource(resourceName, data) {
      var url = BASE_URL + '/' + resourceName + '/' + data.id
      url += '/stream'
      url += '?' + 'min=' + data['minTime']
      url += '&' + 'max=' + data['maxTime']
      return axios.get(url, data)
    }

}
