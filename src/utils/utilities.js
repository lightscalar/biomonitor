window.utils = {}

// Convenience function for SELECT statements.
utils.itemize = function(array) {
  itemizedArray = []
  for (var i=0; i<array.length; i++) {
    itemizedArray.push({text: array[i]})
  }
  return itemizedArray
}


// Break an array into a series of smaller arrays for, e.g., pagination.
utils.chunkArray = function(arr, chunkSize) {
  var arrLen = arr.length
  var numChunks = Math.ceil(arr.length / chunkSize)
  var chunks = []
  var pos = 0
  for (let i=0; i < numChunks; i++) {
    chunk = []
    let size = Math.min(chunkSize, arrLen-pos)
    for (let j=0; j < size; j++) {
      chunk.push(arr[pos+j])
    }
    chunks.push(chunk)
    pos += size
  }
  return chunks
}


// Create a list of numbers from 0... N-1.
utils.range = function(N) {
  arr = []
  for (let k=0; k<N; k++) {
    arr.push(k)
  }
  return arr
}

