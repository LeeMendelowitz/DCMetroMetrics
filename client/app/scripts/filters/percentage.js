'use strict';

/**
 * @ngdoc filter
 * @name dcmetrometricsApp.filter:percentage
 * @function
 * @description
 * # percentage
 * Filter in the dcmetrometricsApp.
 */

angular.module('dcmetrometricsApp')
  .filter('percentage', ['$filter', function ($filter) {
    return function (input, decimals) {
      return $filter('number')(input * 100, decimals) + '%';
    };
  }]);