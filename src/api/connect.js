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

    postResource(resourceName, data) {
      var url = BASE_URL + '/' + resourceName
      return axios.post(url, data)
    }

}
