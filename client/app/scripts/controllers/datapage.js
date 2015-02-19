'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:DatapagCtrl
 * @description
 * # DatapagCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('DataPageCtrl', ['$scope', 'Page', function ($scope, Page) {

    Page.title('DC Metro Metrics: Data');
    Page.description('Download DC Metro Metrics Data. This includes escalator, elevator, and crowdsourced hot car data about the WMATA Metrorail system in Washington, DC.');

  }]);
