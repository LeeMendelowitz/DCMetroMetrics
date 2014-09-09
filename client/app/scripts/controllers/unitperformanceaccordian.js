'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:UnitperformanceaccordianCtrl
 * @description
 * # UnitperformanceaccordianCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('UnitPerformanceAccordianCtrl', function ($scope) {

      $scope.accordianItems = [];
      $scope.oneAtATime = false;
      $scope.dataKeyList = []; // List of Row Names

      var keys = ["all_time", "one_day", "three_day", "seven_day", "fourteen_day", "thirty_day"];
      $scope.keys = keys;
      var headings = ["All Time", "1 Day", "3 Day", "7 Day", "14 Day", "30 Day"]; // Column Names
      $scope.headings = headings;

      $scope.$watch("unitData", function(newVal, oldVal) {

        $scope.accordianItems = [];

        var performanceSummary = $scope.unitData && $scope.unitData.performance_summary;

        if (performanceSummary === undefined) {
          return;
        }

        var i, dk, key, heading, summary, isOpen;

        var dataKeys = {};

        for(i = 0; i < keys.length; i++) {

          key = keys[i];
          heading = headings[i];
          summary = performanceSummary[key];

          isOpen = i === 0;

          if( summary === undefined) {
            continue;
          }

          $scope.accordianItems.push( {
            heading: heading,
            summary: summary,
            isOpen: isOpen
          });

          for(dk in summary) {
            if (summary.hasOwnProperty(dk)) {
              dataKeys[dk] = 1;
            }
          }
        }

       $scope.dataKeyList = [];
        for(dk in dataKeys) {
          if(dataKeys.hasOwnProperty(dk)) {
            $scope.dataKeyList.push(dk);
          }
        }

      });

  });
