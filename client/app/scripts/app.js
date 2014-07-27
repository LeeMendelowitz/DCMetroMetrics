'use strict';

/**
 * @ngdoc overview
 * @name dcmetrometrics
 * @description
 * # dcmetrometrics
 *
 * Main module of the application.
 */
angular
  .module('dcmetrometricsApp', [
    'ngAnimate',
    'ngCookies',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'ngTouch'
  ])
  .config(function ($routeProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'views/main.html',
        controller: 'MainCtrl'
      })
      .when('/about', {
        templateUrl: 'views/about.html',
        controller: 'AboutCtrl'
      })
      .when('/stations', {
        templateUrl: 'views/stationlisting.html',
        controller: 'StationDirectoryCtrl'
      })
      .when('/stations/:station', {
        templateUrl: 'views/station.html',
        controller: 'StationCtrl'
      })
      .otherwise({
        redirectTo: '/'
      });
  });
