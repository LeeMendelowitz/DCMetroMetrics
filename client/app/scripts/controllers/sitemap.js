'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:SitemapCtrl
 * @description
 * # SitemapCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('SitemapCtrl', ["$scope", "$state", "directory", "hotCarDirectory", function ($scope, $state,
    directory, hotCarDirectory) {

    $scope.$state = $state;


    //Get Escalator data
    directory.get_directory().then(function(data) {
      $scope.directory = data;
      $scope.station_names = [];
      $scope.station_short_names = [];
      var station;
      for(var k in $scope.directory.directory) {
        station = $scope.directory.directory[k];
        $scope.station_names.push(k);
        $scope.station_short_names.push(station.short_name);
      }
    });

    directory.get_unit_dict().then(function(data) {
      $scope.unit_dict = data;

      $scope.unit_ids = [];
      for(var k in $scope.unit_dict) {
        $scope.unit_ids.push(k);
      }

    });

    // Get Hotcar data

    hotCarDirectory.get_data().then(function(data) {
      $scope.hot_car_data = data;
      $scope.hot_car_numbers = [];
      for(var k in data.reportsByCar) {
        $scope.hot_car_numbers.push(k);
      }
    });


  }]);
