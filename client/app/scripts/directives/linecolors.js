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
      template: '',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {
        
        // Process the list of line codes, converting the string to 
        // a list
        var $e = $(element);

        scope.$watch("lines", function(lines) {
            // console.log("link watch sees lines: ", lines);
            var lines = scope.lines && scope.lines.replace(/ /g, '').split(",");
            $e.html("");
            if (!lines) return;
            for(var i = 0; i < lines.length; i++) {
              $e.append($('<div class="circle ' + lines[i] + '"></div>'));
            }
        });

        // console.log("link outside watch sees scope.lines: ", scope.lines);
      },
      scope: {
        lines: '@'
      }
    };
  });
