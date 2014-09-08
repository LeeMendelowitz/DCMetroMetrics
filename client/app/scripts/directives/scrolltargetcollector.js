'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:scrollTargetCollector
 * @description
 * # scrollTargetCollector
 */
angular.module('dcmetrometricsApp')
  .directive('scrollTargetCollector', function () {
    return {
      restrict: 'A',
      link: function postLink(scope, element, attrs) {
      },
      controller: ['$scope', '$uiViewScroll', '$timeout', function($scope, $uiViewScroll, $timeout) {

          $scope.watchTargets = {};

          var BODY_OFFSET = 40; // pixels from body top. This should be set somewhere as a global.

          $scope.curScrollTarget = "";

          $scope.registerScrollTarget = function(id, elem) {
            id && elem && ($scope.watchTargets[id] = elem);
          };

          $scope.scrollTo = function(id) {

            var elem = $scope.watchTargets[id];
            if (!elem) { return; }

            var offsetTop = elem.offset().top;

            $timeout( function() {
              $scope.curScrollTarget = id;
              $(document).scrollTop(offsetTop - BODY_OFFSET);
            });



          };

      }]
    };
  });
