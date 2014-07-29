'use strict';

/**
 * @ngdoc filter
 * @name dcmetrometricsApp.filter:unitIdToHuman
 * @function
 * @description
 * # unitIdToHuman
 * Filter in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .filter('unitIdToHuman', function () {
    return function (input) {
      var code = input.substring(0,6);
      var unit_type = input.substring(6);
      unit_type = unit_type.charAt(0).toUpperCase() + unit_type.substring(1).toLowerCase();
      return unit_type + " " + code;
    };
  });
