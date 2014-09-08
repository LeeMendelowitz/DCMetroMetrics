'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:scrollTarget
 * @description
 * # scrollTarget
 */
angular.module('dcmetrometricsApp')
  .directive('scrollTarget', function () {
    return {
      restrict: 'A',
      link: function postLink(scope, element, attrs) {
        var id = attrs.id;
        console.log("scope, elment, attrs: ", scope, element, attrs);
        scope.registerScrollTarget(id, element);
      },
      require: '^scrollTargetCollector'
    };
  });
