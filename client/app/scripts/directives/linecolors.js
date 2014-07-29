'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:lineColors
 * @description
 * # lineColors
 */
angular.module('dcmetrometricsApp')
  .directive('linecolors', function () {
    return {
      template: '<div ng-repeat="line in lines" class = "circle {{line}}"></div>',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {
      },
      scope: {
        lines: '='
      }
    };
  });
