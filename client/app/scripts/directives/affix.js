'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:affix
 * @description
 * # affix
 */
angular.module('dcmetrometricsApp')
  .directive('affix', function () {
    return {
      restrict: 'A',
      link: function postLink(scope, element, attrs) {
          element.affix({
              offset: {
                top: scope.offsetTop
              }
            });
      },
      scope: {
        offsetTop: "@"
      } 
    };
  });
