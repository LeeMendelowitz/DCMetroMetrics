'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:HotcardirectoryCtrl
 * @description
 * # HotcardirectoryCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('HotCarDirectoryCtrl', ['$scope', '$location', '$anchorScroll', 'hotCarDirectory', 'ngTableParams', '$filter',
    function ($scope, $location, $anchorScroll, hotCarDirectory, ngTableParams, $filter) {
  
    var deferred = hotCarDirectory.get_data();

    $scope.section = 'sec-leaderboard';


    $scope.recentReports = undefined;

    // Get HotCar data and put data on the scope.
    deferred.then( function(data) {

      $scope.allReports = data.allReports;
      $scope.data = data;
      $scope.summaryByCar = data.summaryByCar;
      $scope.reportsByCar = data.reportsByCar;
      $scope.allSummaries = data.allSummaries;
      $scope.recentReports = $scope.allReports.slice(0, 20);

    });

   

    // Set up the hot car leaderboard
    $scope.leaderboardTableParams = new ngTableParams({
        page: 1,            // show first page
        count: 10,          // count per page
        sorting: {
            count: 'desc'     // initial sorting
        }
    }, {
        total: 0, // length of data
        getData: function($defer, params) {

            deferred.then( function(data) {

              params.total(data.allSummaries.length);

               // use build-in angular filter
              var orderedData = params.sorting() ?
                                  $filter('orderBy')(data.allSummaries, params.orderBy()) :
                                  data.allSummaries;
              $defer.resolve(orderedData.slice((params.page() - 1) * params.count(), params.page() * params.count()));

            });
        }

    });

    $scope.scrollTo = function(id) {

        // set the location.hash to the id of
        // the element you wish to scroll to.
        $scope.section = id;
        $location.hash(id);
        $anchorScroll();

    };




  }]);
