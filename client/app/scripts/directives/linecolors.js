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
      template: '<div ng-repeat="line in lineList" class="circle {{line}}"></div>',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {
        
        // Process the list of line codes, converting the string to 
        // a list

        scope.lineList = [];

        scope.$watch("lines", function(lines){
          scope.lineList = [];
          if (scope.lines) { scope.lineList = scope.lines.replace(/ /g, '').split(","); }
        });


        //// COMMENT
        // var $e = $(element);

        // scope.$watch("lines", function(lines) {
        //     // console.log("link watch sees lines: ", lines);
        //     var lines = scope.lines && scope.lines.replace(/ /g, '').split(",");
        //     $e.html("");
        //     if (!lines) return;
        //     for(var i = 0; i < lines.length; i++) {
        //       $e.append($('<div class="circle ' + lines[i] + '"></div>'));
        //     }
        // });
        //// END COMMENT

        // console.log("link outside watch sees scope.lines: ", scope.lines);
      },
      scope: {
        lines: '@'
      },
      replace: true
    };
  });
