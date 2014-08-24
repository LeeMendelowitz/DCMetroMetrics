'use strict';

/**
 * @ngdoc filter
 * @name dcmetrometricsApp.filter:capFirst
 * @function
 * @description
 * # capFirst
 * Filter in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .filter('capFirst', function () {
    return function (input) {
      
      var splitWords = input.toLowerCase().split(" ");
      var splitWordsCap = splitWords.map(function(word) {
        return word[0].toUpperCase() + word.slice(1);
      })

      return splitWordsCap.join(" ");
      
    };
  });
