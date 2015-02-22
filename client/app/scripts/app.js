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
    'mgcrea.ngStrap.tooltip',
    'mgcrea.ngStrap.helpers.debounce',
    'ui.bootstrap',
    'ngTable',
    'tableSort',
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
  
app.config(function($stateProvider, $urlRouterProvider, $urlMatcherFactoryProvider) {
  

  // For any unmatched url, redirect to /state1
  $urlRouterProvider.otherwise("/home");

  // Do not require trailing slashes
  $urlMatcherFactoryProvider.strictMode(false);

  //
  // Now set up the states
  $stateProvider
    .state('home', {
      url: "/home",
      templateUrl: "/views/main.html",
      controller: 'OutagesCtrl'
    })
    .state('about', {
      url: "/about",
      templateUrl: "/views/about.html",
      controller: "AboutCtrl"
    })
    .state('dashboard', {
      url: "/dashboard",
      templateUrl: "/views/dashboard.html",
      controller: 'OutagesCtrl'
    })
    .state('sitemap', {
      url: "/sitemap",
      templateUrl: "views/sitemap.html",
      controller: 'SitemapCtrl'
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
    .state('unit.calendar', {
      url: '/calendar'
    })
    .state('rankings', {
      url: '/rankings?timePeriod&unitType&searchString&orderBy',
      templateUrl: '/views/rankings.html',
      controller: 'RankingsCtrl',
      reloadOnSearch: false // Search params will change frequently in this state as filters are applied to the rankings table.
    })
    // Was having trouble here, needed the abstract parent view to get
    // this to work!
    .state('dailyservicereport', {
      url: '/dailyservicereport/:day',
      templateUrl: '/views/dailyservicereport.html',
      controller: 'DailyServiceReportCtrl'
    })
    .state('press', {
      url: '/press',
      templateUrl: '/views/press.html',
      controller: 'PressCtrl'
    })
    .state('data', {
      url: '/data',
      templateUrl: '/views/data.html',
      controller: 'DataPageCtrl'
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

app.run(['$anchorScroll', function($anchorScroll) {
  $anchorScroll.yOffset = 60;   // always scroll by 50 extra pixels
}]);

// Hack to fix date picker
// https://github.com/angular-ui/bootstrap/issues/2659
app.directive('datepickerPopup', function (){
  return {
    restrict: 'EAC',
    require: 'ngModel',
    link: function(scope, element, attr, controller) {
      //remove the default formatter from the input directive to prevent conflict
      controller.$formatters.shift();
    }
  };
});

