'use strict';

/**
 * @ngdoc overview
 * @name dcmetrometrics
 * @description
 * # dcmetrometrics
 *
 * Main module of the application.
 */
var app = angular
  .module('dcmetrometricsApp', [
    'ngAnimate',
    'ngCookies',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'ngTouch',
    'mgcrea.ngStrap',
    'mgcrea.ngStrap.helpers.dimensions',
    'mgcrea.ngStrap.scrollspy',
    'ui.bootstrap',
    'ngTable',
    'angular-loading-bar',
    'angularSpinner',
    'ui.utils',
    'ui.router'
  ]);

app.config(function($locationProvider) {
  $locationProvider.html5Mode({
    enabled: true,
    requireBase: false
  });
});
  
app.config(function($stateProvider, $urlRouterProvider) {
  //
  // For any unmatched url, redirect to /state1
  $urlRouterProvider.otherwise("/home");
  //
  // Now set up the states
  $stateProvider
    .state('home', {
      url: "/home",
      templateUrl: "/views/main.html",
      controller: 'OutagesCtrl'
    })
    .state('outages', {
      url: "/outages",
      templateUrl: '/views/outages.html',
      controller: 'OutagesCtrl'
    })
    .state('outages.escalators', {
      url: "/escalators",
    })
    .state('outages.elevators', {
      url: "/elevators",
    })
    .state('stations', {
      abstract: true,
      url: '/stations',
      template: '<ui-view/>'
    })
    .state('stations.list', {
      url: '/list',
      templateUrl: '/views/stationlisting.html',
      controller: 'StationDirectoryCtrl'
    })
    .state('stations.detail', {
      url: '/detail/:station',
      templateUrl: '/views/station.html',
      controller: 'StationCtrl'
    })
    .state('stations.detail.escalators', {
      url: '/escalators'
    })
    .state('stations.detail.elevators', {
      url: '/elevators'
    })
    .state('stations.detail.recent', {
      url: '/recent'
    })
    .state('hotcars', {
      abstract: true,
      url: '/hotcars',
      controller: 'HotCarDirectoryCtrl',
      template: '<ui-view/>'
    })
    .state('hotcars.main', {
      url: '/main',
      templateUrl: '/views/hotcars.html'
    })
    .state('hotcars.main.leaderboard', {
      url: '/leaderboard'
    })
    .state('hotcars.main.tweets', {
      url: '/tweets'
    })
    .state('hotcars.main.timeseries', {
      url: '/timeseries'
    })
    .state('hotcars.detail', {
      url: '/detail/:carNumber',
      templateUrl: '/views/hotcarpage.html',
      controller: 'HotcarpageCtrl'
    })
    .state('unit', {
      url: '/unit/:unitId',
      templateUrl: '/views/unit.html',
      controller: 'UnitPageCtrl'
    })
    .state('unit.summary', {
      url: '/summary'
    })
    .state('unit.statuses', {
      url: '/statuses'
    })
    .state('rankings', {
      url: '/rankings?timePeriod&unitType&searchString&orderBy',
      templateUrl: '/views/rankings.html',
      controller: 'RankingsCtrl',
      reloadOnSearch: false // Search params will change frequently in this state as filters are applied to the rankings table.
    });

});


app.config(['cfpLoadingBarProvider', function(cfpLoadingBarProvider) {
    cfpLoadingBarProvider.latencyThreshold = 100;
}]);

app.run(
  [          '$rootScope', '$state', '$stateParams',
    function ($rootScope,   $state,   $stateParams) {
      // It's very handy to add references to $state and $stateParams to the $rootScope
      // so that you can access them from any scope within your applications.
      $rootScope.$state = $state;
      $rootScope.$stateParams = $stateParams;
    }
  ]
);
