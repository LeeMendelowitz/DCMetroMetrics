'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:OutagesCtrl
 * @description
 * # OutagesCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('OutagesCtrl', ['$scope', '$route', '$location', 'directory', 'statusTableUtils', 

     function ($scope, $route, $location, directory, statusTableUtils) {

      $scope.directory = directory;
      $scope.statusTableUtils = statusTableUtils;

      // Get the unit directory
      directory.get_directory().then( function(data) {

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


        // Get recent statuses
        directory.get_recent_updates().then( function(data) {
          $scope.recentUpdates = data;
        });

      });




      // Figure out which tab is active based on the location.
      $scope.escalatorTabActive = true;
      $scope.elevatorTabActive = false;
      var reElevator = /elevator/i;
      if ( reElevator.test($location.path()) ) {
        $scope.escalatorTabActive = false;
        $scope.elevatorTabActive = true;
      }

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

      $scope.unitDescription = function(unit){
        var ret = "";
        if (!unit) { return undefined; }
        if (unit.station_desc) {
          ret = unit.station_desc + ", " + unit.esc_desc;
        } else {
          ret = unit.esc_desc;
        }
        return ret;
      };

      $scope.selectEscalatorTab = function() {
        console.log("selected escalator tab");
        //$location.path('/outages/escalator');
      };

      $scope.selectElevatorTab = function() {
        console.log("selected elevator tab");
        //$location.path('/outages/elevator');
      };


     }]);

