'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:HeadCtrl
 * @description
 * # HeadCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('HeadCtrl', ['$scope', '$rootScope', 'Page', function ($scope, $rootScope, Page) {
    $scope.Page = Page;

    // Let's listen to some events on the rootScope for debugging
    $rootScope.$on('$viewContentLoaded', function(event, data) {
      console.log('Got event! ', event, data);
    });

    $rootScope.$on('viewContentLoaded', function(event, data) {
      console.log('Got event! ', event, data);
    });

  }]);
