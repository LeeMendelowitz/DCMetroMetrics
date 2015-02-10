'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:OutagesCtrl
 * @description
 * # OutagesCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('OutagesCtrl', ['$scope', '$uiViewScroll', '$location', '$state', 'directory', 'statusTableUtils', 

     function ($scope, $uiViewScroll, $location, $state, directory, statusTableUtils) {

      $scope.directory = directory;
      $scope.statusTableUtils = statusTableUtils;
      $scope.elevatorOutages = undefined;
      $scope.escalatorOutages = undefined;
      $scope.dailyBreakCount = undefined;
      $scope.dailyBrokenCount = undefined;
      $scope.dailyBreakCountHeatCal = undefined;
      $scope.dailyBrokenCountHeatCal = undefined;

      // Get the unit directory
      directory.get_directory().then( function(data) {

        var i, key, outage;

        // Sort the outages by station name and unit code.
        var sortFunc = function(unit1, unit2) {
          var s1 = directory.getStationName(unit1);
          var s2 = directory.getStationName(unit2);
          
          if (s1 < s2) {
            return -1;
          } else if (s2 < s1) {
            return 1;
          }

          // Station match, sort by code.
          if(s1.unit_id < s2.unit_id) {
            return -1;
          } else {
            return 1;
          }

        };

        $scope.data = data;
        $scope.escalatorOutages = data.escalatorOutages.sort(sortFunc);
        $scope.elevatorOutages = data.elevatorOutages.sort(sortFunc);
        $scope.unitIdToUnit = data.unitIdToUnit;

        // Count how many station outages there are.
        var stationDict = {};
        for(i = 0; i < data.escalatorOutages.length; i++) {
          outage = data.escalatorOutages[i];
          stationDict[outage.station_name] = 1;
        }
        for(i = 0; i < data.elevatorOutages.length; i++) {
          outage = data.elevatorOutages[i];
          stationDict[outage.station_name] = 1;
        }

        var stations_with_outage = [];
        for(key in stationDict) {
          if(stationDict.hasOwnProperty(key)) {
            stations_with_outage.push(key);
          }
        }

        $scope.stations_with_outage = stations_with_outage;


        // Get recent statuses
        directory.get_recent_updates().then( function(data) {
          $scope.recentUpdates = data;
          $scope.mostRecent = $scope.recentUpdates[0];
        });


        // Get outage counts.

        var convertDailyCountsForHeatCal = function(d) {
          var ret = {};
          var num, k, new_k;
          for(k in d) {
            if(d.hasOwnProperty(k)) {
              new_k = moment(k).unix();
              ret[new_k] = d[k];
            }
          }
          return ret;

        };

        directory.get_daily_break_count().then( function(data) {
          $scope.dailyBreakCount = data;
          $scope.dailyBreakCountHeatCal = {
            escalators: convertDailyCountsForHeatCal(data.escalators),
            elevators: convertDailyCountsForHeatCal(data.elevators)
          }
        });

        directory.get_daily_broken_count().then( function(data) {
          $scope.dailyBrokenCount = data;
          $scope.dailyBrokenCountHeatCal = {
            escalators: convertDailyCountsForHeatCal(data.escalators),
            elevators: convertDailyCountsForHeatCal(data.elevators)
          }
        });

      });



      $scope.getSymptomClass = function(unit) {

          var catToClass = {
            BROKEN : 'danger',
            INSPECTION : 'warning',
            OFF : 'danger',
            ON : 'success',
            REHAB : 'info'
          };

          var category = unit.key_statuses.lastStatus.symptom_category;
          return catToClass[category];

      };


      $scope.showEscalators = function() {
        return $scope.$state.is("outages.escalators") ||
          $scope.$state.is("outages");
      };

      $scope.showElevators = function() {
        return $scope.$state.is("outages.elevators");
      };

      $scope.getMostRecentOutageTime = function() {

      }



     }]);

