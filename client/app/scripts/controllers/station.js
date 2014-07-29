'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:StationCtrl
 * @description
 * # StationCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')

  .controller('StationCtrl', ['$scope', '$route', 'directory', 'statusTableUtils', 

     function ($scope, $route, directory, statusTableUtils) {

        $scope.$route = $route;
        $scope.statusTableUtils = statusTableUtils;
        $scope.stationName = $route.current.params.station;

        $scope.escalators_have_station_descriptions = false;
        $scope.elevators_have_station_descriptions = false;


        // Request station directory data
        directory.get_directory().then( function(data) { 
          var i;
          console.log("Got data!");
          $scope.stationDirectory = data.directory;
          $scope.stationData = data.shortNameToData[$scope.stationName];

          var escalators = $scope.stationData.escalators;
          for(i = 0; i < escalators.length; i++) {
            if (escalators[i].station_desc) {
              $scope.escalators_have_station_descriptions = true;
              break;
            }
          }

          var elevators = $scope.stationData.elevators;
          for(i = 0; i < elevators.length; i++) {
            if (elevators[i].station_desc) {
              $scope.elevators_have_station_descriptions = true;
              break;
            }
          }


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

  }]);
