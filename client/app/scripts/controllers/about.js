'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:AboutCtrl
 * @description
 * # AboutCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('AboutCtrl', ['$scope', 'Page', function ($scope, Page) {

    Page.title('DC Metro Metrics: About');
    Page.description('About the DC Metro Metrics website. What is it? How did it get started? Who can I contact? Where is the source code?');

  }]);
