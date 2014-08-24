'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:UnitentryCtrl
 * @description
 * # UnitentryCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('UnitentryCtrl', ['$scope', 'directory', function ($scope, directory) {

    // Get the unit from the status for the current scope.
    $scope.stationLines = directory.getStationLines($scope.unit);

  }]);
