'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:scrollToBookmark
 * @description
 * # scrollToBookmark
 */
angular.module('dcmetrometricsApp')
  .directive('scrollToBookmark', function () {

    return {
      restrict: 'A',
      link: function(scope, element, attrs) {
        var value = attrs.scrollToBookmark;
        element.click(function() {
          scope.$apply(function() {
            var selector = "[scroll-bookmark='"+ value +"']";
            var element = $(selector);
            if(element.length) {
              window.scrollTo(0, element[0].offsetTop - 100);  // Don't want the top to be the exact element, -100 will go to the top for a little bit more
            }
          });
        });
      }
    };

  });


