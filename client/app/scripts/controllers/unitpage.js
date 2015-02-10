'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:UnitCtrl
 * @description
 * # UnitCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('UnitPageCtrl', ['$scope', 'Page', '$stateParams', '$filter', 'unitService', 'directory', 'statusTableUtils', 'UnitStatus',
    function ($scope, Page, $stateParams, $filter, unitService, directory, statusTableUtils, UnitStatus) {


      Page.title("DC Metro Metrics: " + $stateParams.unitId);
      Page.description(" ");


      $scope.unitId = $stateParams.unitId;
      $scope.statusTableUtils = statusTableUtils;



      unitService.getUnitData($scope.unitId).then( function(data) {

        console.log("have unit data: ", data);
        $scope.unitData = data;
        $scope.unit = $scope.unitData;
        $scope.key_statuses = $scope.unitData.key_statuses;
        var stationCode = data.station_code;

        // Get the station data for this unit.
        directory.get_directory().then(function(stationDirectory) {
          console.log("Have directory data: ", stationDirectory);
          $scope.stationData = stationDirectory.codeToData[stationCode];
          Page.description("Performance history for " + $filter('unitIdToHuman')($scope.unitId) + " at " + $scope.stationData.long_name + " station in the WMATA Metrorail system in Washington, DC.");

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
