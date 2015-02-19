  'use strict';

/**
 * @ngdoc filter
 * @name dcmetrometricsApp.filter:duration
 * @function
 * @description
 * # duration
 * Filter in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .filter('duration', function () {
    return function (input) {
      
      // Input is in milliseconds. Convert to seconds.
      var seconds = parseInt(input)/1000.0;
      var days = 0, hours = 0, minutes = 0;
      var remainder = seconds;

      if (remainder >= 3600*24) {
        days = Math.floor(remainder/(3600 * 24));
        remainder = remainder - days*3600*24;
      }

      if (remainder >= 3600) {
        hours = Math.floor(remainder/3600.0);
        remainder = remainder - hours*3600;
      }

      if (remainder >= 60) {
        minutes = Math.floor(remainder/60.0);
        remainder = remainder - minutes*60;
      }

      var ret = "";
      if (days) {
        ret = ret + days + "d";
      }
      if (hours) {
        ret = ret + " " + hours + "h";
      }

      ret = ret + " " + minutes + "m";
      
      return ret;
      
    };
  });
