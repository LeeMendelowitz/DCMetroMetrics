'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:UnitCtrl
 * @description
 * # UnitCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('UnitPageCtrl', ['$scope', '$stateParams', 'unitService', 'directory', 'statusTableUtils', 'UnitStatus',
    function ($scope, $stateParams, unitService, directory, statusTableUtils, UnitStatus) {

      $scope.unitId = $stateParams.unitId;
      $scope.statusTableUtils = statusTableUtils;



      unitService.getUnitData($scope.unitId).then( function(data) {

        console.log("have unit data: ", data);
        $scope.unitData = data;
        $scope.unit = $scope.unitData.unit;
        $scope.key_statuses = $scope.unitData.unit.key_statuses;
        var stationCode = data.unit.station_code;

        // Get the station data for this unit.
        directory.get_directory().then(function(stationDirectory) {
          console.log("Have directory data: ", stationDirectory);
          $scope.stationData = stationDirectory.codeToData[stationCode];
        });
      });



      $scope.showSummary = function() {
        return $scope.$state.is("unit") ||
          $scope.$state.is("unit.summary");
      };

      $scope.showStatuses = function() {
        return $scope.$state.is("unit.statuses");
      };

      $scope.showCalendar = function() {
        return $scope.$state.is("unit.calendar");
      };


  }]);
