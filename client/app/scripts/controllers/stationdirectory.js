'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:StationdirectoryCtrl
 * @description
 * # StationdirectoryCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('StationDirectoryCtrl', ['$scope', 'directory', function ($scope, directory) {


    // Request station directory data
    directory.get_directory().then( function(data) { 
      console.log("Got data!");
      $scope.stationDirectory = data.directory;

    });



  }]);
