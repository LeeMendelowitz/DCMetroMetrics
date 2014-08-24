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

      // Capitalize the first letter of
      // each element in array. Return as list.
      var capFirst = function(a) {
        return a.map(function(word) {
          return word[0].toUpperCase() + word.slice(1).toLowerCase();
        });
      };

      var ret = input.split(" ");
      ret = ret.map(function(e) { 
        var a = e.split("/");
        return capFirst(a);
      });

      // Join on "/"
      ret = ret.map(function(e) { return e.join("/");});
      ret = ret.join(" ");
      return ret;
    
    };

  });
