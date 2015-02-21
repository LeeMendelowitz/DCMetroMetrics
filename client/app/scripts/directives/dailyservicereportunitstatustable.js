'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:dailyServiceReportUnitStatusTable
 * @description
 * # dailyServiceReportUnitStatusTable
 */
angular.module('dcmetrometricsApp')
  .directive('dailyservicereportunitstatustable', function () {
    return {
      templateUrl: "/views/dailyservicereportunitstatustable.html",
      restrict: 'E',
      scope: {
        statuses: '='
      }
    };
  });
