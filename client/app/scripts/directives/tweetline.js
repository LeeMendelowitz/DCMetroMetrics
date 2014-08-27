'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:tweetline
 * @description
 * # tweetline
 */
angular.module('dcmetrometricsApp')
  .directive('tweetline', function () {

    return {

      template: '<div></div>',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {

        var i, $tweet_div, $tweet, report;

        console.log("scope: ", scope);
        console.log("scope.reports: ", scope.reports);

        scope.$watch('reports', function(reports) {

          if (!reports) return;

          if (!twttr) {
            console.log("No twttr!");
            return;
          }

          console.log('twttr: ', twttr);

          console.log("inside watch on reports");
          console.log("reports in watch: ", reports);

          for(i = 0; i < reports.length; i++){

            report = reports[i];

            $tweet_div = $('<div class="tweet-wrapper col-xs-12 col-sm-6 col-md-4 col-lg-3"></div>');
            $tweet = $("<div></div>");
            $tweet.append($(report.tweet.embed_html));
            $tweet_div.append($tweet);
            $(element).append($tweet_div);

            if ((i+1)%2 == 0)  $(element).append($('<div class="clearfix visible-sm-block"></div>'));
            if ((i+1)%3 == 0)  $(element).append($('<div class="clearfix visible-md-block"></div>'));
            if ((i+1)%4 == 0)  $(element).append($('<div class="clearfix visible-lg-block"></div>'));
   

          }

          $(element).append($('<div class="clearfix"></div>'));

          twttr.widgets.load();

        });

      },
      scope: {
        reports: '='
      },
      replace: true
    };
  });
