window.utils = {}

// Convenience function for SELECT statements.
utils.itemize = function(array) {
  itemizedArray = []
  for (var i=0; i<array.length; i++) {
    itemizedArray.push({text: array[i]})
  }
  return itemizedArray
}

