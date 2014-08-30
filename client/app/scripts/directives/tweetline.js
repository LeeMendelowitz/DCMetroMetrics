'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:tweetline
 * @description
 * # tweetline
 */
angular.module('dcmetrometricsApp')
  .directive('tweetline', ['$compile', 'usSpinnerService', function ($compile, usSpinnerService) {

    return {

      templateUrl: 'views/tweetlinepartial.html',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {

          scope.$watch('reports', function(reports, reportsOld) {

            if( reports.length === 0) {
              usSpinnerService.stop('tweet-spinner');
            }
            
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
                usSpinnerService.stop('tweet-spinner');
                $scope.postLoad();
              }
            );
          });

          twttr.widgets.load();

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