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
      template: '<div ng-repeat="line in lineList" class = "circle {{line}}"></div>',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {
        
        // Process the list of line codes, converting the string to 
        // a list
        scope.lineList = scope.lines() && scope.lines().replace(/ /g, '').split(",");

      },
      scope: {
        lines: '&'
      }
    };
  });
