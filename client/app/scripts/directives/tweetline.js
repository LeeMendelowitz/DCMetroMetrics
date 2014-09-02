'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:tweetline
 * @description
 * # tweetline
 */
angular.module('dcmetrometricsApp')
  .directive('tweetline', ['$compile', '$timeout', 'usSpinnerService', function ($compile, $timeout, usSpinnerService) {

    return {

      templateUrl: 'views/tweetlinepartial.html',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {

          scope.$watch('reports', function(reports, reportsOld) {

            if (reports === undefined) { return; }

            if( (reports instanceof Array) && reports.length === 0) {
              usSpinnerService.stop('tweet-spinner');
            }
            
            scope.$evalAsync(function() {
                scope.renderTweets();
            });

          });

          // Create a timeout to show the tweets. This is done to avoid
          // the case where twttr widgets takes to long to load or do its stuff.
          scope.delayedShow = $timeout(function() {
            console.log("doing a delayed show because twttr widgets took too long.");
            scope.showTweets();
          }, 2000);
      },
      controller: ['$scope', function($scope) {

        $scope.renderedTweets = false;

        $scope.showTweets = function() {
          $scope.$apply( function() {
            $scope.renderedTweets = true;
            usSpinnerService.stop('tweet-spinner');
            $scope.postLoad();
          });

          // Cancel the timeout
          $timeout.cancel($scope.delayedShow);

        };

        $scope.renderTweets = function() {

          // Use the Twitter widgets.js to style the tweets
          twttr.events && twttr.events._handlers && twttr.events.unbind &&twttr.events.unbind('loaded');
          twttr.events && twttr.events.bind && twttr.events.bind('loaded', function (event) {
            $scope.showTweets();
          });

          twttr.widgets && twttr.widgets.load();

        };

        var color2code = {
          "RED" : "RD",
          "ORANGE" : "OR",
          "GREEN" : "GR",
          "YELLOW" : "YL",
          "BLUE" : "BL",
          "SILVER": "SV"
        };

        $scope.colorStringFromReport = function(report) {
          var colorString = '';
          if (report.color && color2code.hasOwnProperty(report.color)) {
            colorString += color2code[report.color];
          }
          return colorString;
        }


      }],
      scope: {
        reports: '=',
        postLoad: '&',
        showLink: '='
      }
    };
  }]);