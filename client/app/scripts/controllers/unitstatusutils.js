'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:UnitstatusutilsCtrl
 * @description
 * # UnitstatusutilsCtrl
 * Controller of the dcmetrometricsApp. It adds some useful
 * methods to the scope for working with unit and status things.
 */
angular.module('dcmetrometricsApp')
  .controller('UnitstatusutilsCtrl', ['$scope', 'directory', function ($scope, directory) {

    // Expose methods from the directory service
    $scope.utils = directory;

  }]);
