'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:StationdirectoryCtrl
 * @description
 * # StationdirectoryCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('StationDirectoryCtrl', ['$scope', 'Page', 'directory', function ($scope, Page, directory) {

    Page.title('DC Metro Metrics: Station Listing');
    Page.description('List of all stations in the in the WMATA Metrorail system in Washington, DC.');

    // Request station directory data
    directory.get_directory().then( function(data) { 
      $scope.stationDirectory = data.directory;

    });



  }]);
