'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:HotcarpageCtrl
 * @description
 * # HotcarpageCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('HotcarpageCtrl', ['$scope', '$stateParams', 'hotCarDirectory',
    function ($scope, $stateParams, hotCarDirectory) {

    $scope.$stateParams = $stateParams;
    console.log("have state params: ", $stateParams);
    $scope.carNumber = $stateParams.carNumber;
    $scope.reports = undefined;
    $scope.colors = [];
    $scope.colorString = "";
    $scope.loadedTweets = false;

    $scope.postLoad = function() {
        $scope.loadedTweets = true;
    };

    hotCarDirectory.get_data().then( function(data) {

      // console.log("got all reports: ", data.allReports);

      // Filter to reports for the given car
      // $scope.reports = data.allReports.filter(function(report) {
      //   return report.car_number == $scope.carNumber;
      // });

      $scope.reports = undefined;


      if (!data.reportsByCar.hasOwnProperty($scope.carNumber)) {

        // There are no reports for this car.
        $scope.reports = [];
        $scope.postLoad();
        return;

      }
      
      $scope.reports = data.reportsByCar[$scope.carNumber];

      var color2code = {
        "RED" : "RD",
        "ORANGE" : "OR",
        "GREEN" : "GR",
        "YELLOW" : "YL",
        "BLUE" : "BL",
        "SILVER": "SV"
      };

      var co = {}, colorCode, report; 
      $scope.colors = [];
      for(var i = 0; i < $scope.reports.length; i++) {
        report = $scope.reports[i];
        if(report.color && !co.hasOwnProperty(report.color)) {
          colorCode = color2code[report.color];
          if(colorCode) {
            $scope.colors.push(colorCode);
            co[report.color] = 1;
          }
        }
      }

      $scope.colorString = $scope.colors.join();

    });


  }]);
