'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:NavCtrl
 * @description
 * # NavCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')

  .controller('NavCtrl', function ($scope) {

    $scope.navbarCollapsed = true;

    $scope.toggleNav = function() {
      $scope.navbarCollapsed = !$scope.navbarCollapsed;
    };

    $scope.collapseNav = function() {
      $scope.navbarCollapsed = true;
    }

  });
