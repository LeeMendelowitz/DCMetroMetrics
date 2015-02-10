'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:HeadCtrl
 * @description
 * # HeadCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('HeadCtrl', ['$scope', 'Page', function ($scope, Page) {
    $scope.Page = Page;
  }]);
