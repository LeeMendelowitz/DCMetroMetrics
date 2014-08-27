'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:HotcarpageCtrl
 * @description
 * # HotcarpageCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('HotcarpageCtrl', ['$scope', '$route', 'hotCarDirectory', function ($scope, $route, hotCarDirectory) {

    $scope.$route = $route;
    $scope.carNumber = $route.current.params.carNumber;
    $scope.reports = [];
    $scope.colors = [];
    $scope.colorString = "";

    hotCarDirectory.get_data().then( function(data) {

      // console.log("got all reports: ", data.allReports);

      // Filter to reports for the given car
      // $scope.reports = data.allReports.filter(function(report) {
      //   return report.car_number == $scope.carNumber;
      // });


      if (!data.reportsByCar.hasOwnProperty($scope.carNumber)) return;
      
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
