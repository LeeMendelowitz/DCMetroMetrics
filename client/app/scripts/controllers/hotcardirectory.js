'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:HotcardirectoryCtrl
 * @description
 * # HotcardirectoryCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('HotCarDirectoryCtrl', ['$scope', 'hotCarDirectory', function ($scope, hotCarDirectory) {
  
    console.log("hot car controller requesting data.");
    
    hotCarDirectory.get_data().then( function(data) {

      console.log("got all reports: ", data.allReports);
      $scope.allReports = data.allReports;

    });

  }]);
