'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:StatusentryCtrl
 * @description
 * # StatusentryCtrl
 * Controller of the dcmetrometricsApp
 * Extract some useful things from a status.
 */
angular.module('dcmetrometricsApp')
  .controller('StatusentryCtrl', ['$scope', 'directory', function ($scope, directory) {

    // Get the unit from the status for the current scope.
    $scope.unit = undefined;
    $scope.stationLines = undefined;

    // We can simply assume that a controller has initialized
    // the directory and recent_upates data before this controller 
    // is initialized.

    // directory.get_directory().then(function(data) {
    //   directory.get_recent_updates().then(function(data) {

        $scope.unit = directory.unitFromStatus($scope.status);
        $scope.stationLines = directory.getStationLinesForStatus($scope.status);

    //   });
    // });

  }]);
