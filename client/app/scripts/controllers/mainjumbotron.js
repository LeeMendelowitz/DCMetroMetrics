'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:MainjumbotronCtrl
 * @description
 * # MainjumbotronCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('MainJumbotronCtrl', ['$scope', '$location', '$anchorScroll', function ($scope, $location, $anchorScroll) {
      
      $scope.$location = $location;
      $scope.$anchorScroll = $anchorScroll;

      $scope.goToOutageCalendar = function() {

        // set the location.hash to the id of
        // the element you wish to scroll to.
        $location.hash('dcmm-escalator-outage-calendar');

        // call $anchorScroll()
        $anchorScroll();
      };

  }]);
