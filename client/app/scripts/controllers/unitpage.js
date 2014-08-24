'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:UnitCtrl
 * @description
 * # UnitCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('UnitPageCtrl', ['$scope', '$route', 'unitService', 'directory', 'statusTableUtils',
    function ($scope, $route, unitService, directory, statusTableUtils) {

      $scope.$route = $route;
      $scope.unitId = $route.current.params.unitId;
      $scope.statusTableUtils = statusTableUtils;


      unitService.getUnitData($scope.unitId).then( function(data) {
        console.log("have unit data: ", data);
        $scope.unitData = data;
        var stationCode = data.unit.station_code;

        // Get the station data for this unit.
        directory.get_directory().then(function(stationDirectory) {
          console.log("Have directory data: ", stationDirectory);
          $scope.stationData = stationDirectory.codeToData[stationCode];
        });
      });


  }]);
