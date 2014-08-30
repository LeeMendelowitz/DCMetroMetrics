'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:tweetline
 * @description
 * # tweetline
 */
angular.module('dcmetrometricsApp')
  .directive('tweetline', ['$compile', function ($compile) {

    return {

      templateUrl: 'views/tweetlinepartial.html',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {

          scope.$watch('reports', function(reports, reportsOld) {
            
            scope.$evalAsync(function() {
                scope.renderTweets();
            });

          });
      },
      controller: ['$scope', function($scope) {

        $scope.renderedTweets = false;

        $scope.renderTweets = function() {
          // Use the Twitter widgets.js to style the tweets

          twttr.events._handlers = {}; // unbind all twitter events
          twttr.events.bind('loaded', function (event) {
            //console.log('twitter load');
            $scope.$apply(function() {
              $scope.renderedTweets = true;
                $scope.postLoad();
              }
            );
          });

          twttr.widgets.load();

        };


      }],
      scope: {
        reports: '=',
        postLoad: '&'
      },
      replace: true
    };
  }]);