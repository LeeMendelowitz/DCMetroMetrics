'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:RankingsCtrl
 * @description
 * # RankingsCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('RankingsCtrl', ['$scope', '$state', 'directory', 'ngTableParams', '$filter',
    '$timeout', '$stateParams', '$location',

     function ($scope, $state, directory, ngTableParams, $filter, $timeout, $stateParams, $location) {

      console.log("RankingsCtrl top!");

      $scope.filtersAreCollapsed = false;
      $scope.tableInitialized = false;

      $scope.showFilters = function() { 
        $scope.filtersAreCollapsed = false;
      };

      $scope.hideFilters = function() { 
        $scope.filtersAreCollapsed = true;
      };

      $scope.toggleFilters = function() { 
        $scope.filtersAreCollapsed = !$scope.filtersAreCollapsed;
      };

      $scope.rankingsPeriod = $scope.$stateParams.timePeriod || "all_time";
      $scope.searchString = $scope.$stateParams.searchString || "";
      $scope.unitTypes = $scope.$stateParams.unitType || "all_types";

      $scope.resetFilters = function() {
        $scope.rankingsPeriod = "all_time";
        $scope.unitTypes = "all_types";
        $scope.searchString = "";
      };

      $scope.filtersArePristine = function() {
        return $scope.rankingsPeriod === "all_time" &&
               $scope.unitTypes === "all_types" &&
               $scope.searchString === "";
      };

      var reportsFilter = function(data, index) {
        var keep_escalators = $scope.unitTypes === "all_types" || $scope.unitTypes === "escalators_only";
        var keep_elevators = $scope.unitTypes === "all_types" || $scope.unitTypes === "elevators_only";
        return (data.unit_type === "ESCALATOR" && keep_escalators) ||
               (data.unit_type === "ELEVATOR" && keep_elevators);
      };

      $scope.directory = directory;

      var copyFromInto = function(from, to) {
        for (var key in from) {
          if (from.hasOwnProperty(key)) {
            to[key] = from[key];
          }
        }
      };

      ///////////////////////////////////////////////////////////////
      // Sort the records, compute ranks, and apply filter criteria.
      var orderAndFilterData = function(records) {

        var orderedData = $scope.tableParams.sorting() ?
                    $filter('orderBy')(records, $scope.tableParams.orderBy()) :
                    records;

        // Assign ranks
        var i, record;
        for(i = 0; i < orderedData.length; i++) {
          record = orderedData[i];
          record.rank = i + 1;
        }

        // Apply filters
        var filtered_records = $filter('filter')(orderedData, reportsFilter);
        filtered_records = $filter('filter')( filtered_records, {$: $scope.searchString} );
        $scope.filtered_records = filtered_records;
        $scope.have_filtered_records = filtered_records.length > 0;
        return filtered_records;
      };

      // Get the unit directory
      $scope.rankings = {};
      $scope.records = [];  

      var deferred = directory.get_directory();

      $scope.deferred = deferred;

      deferred.then( function(data) {

        $scope.data = data;

        var getRankings = function(rankings_key) {

          
          var unit_data, station_data, unit, record;
          var records = [];

          for(var unitId in data.unitIdToUnit) {

            if(!data.unitIdToUnit.hasOwnProperty(unitId)) {
              continue;
            }

            unit_data = data.unitIdToUnit[unitId];
            station_data = data.codeToData[unit_data.station_code];

            record = {unit_id: unit_data.unit_id,
                      unit_type: unit_data.unit_type,
                      station: station_data.long_name,
                      station_code: unit_data.station_code,
                      station_lines: station_data.all_lines };
            
            // Copy attributes from the all_time performance summary into the record
            copyFromInto(unit_data.performance_summary[rankings_key], record);

            records.push(record);

          }

          $scope.rankings[rankings_key] = records;

          return(records);

        };

        getRankings('all_time');
        getRankings('one_day');
        getRankings('three_day');
        getRankings('seven_day');
        getRankings('fourteen_day');
        getRankings('thirty_day');

      });



      $scope.tableParams = new ngTableParams({
          page: 1,            // show first page
          count: 20,           // count per page
          sorting: {
            broken_time_percentage: 'desc'
          }
        }, {
          total: 0, // length of data
          getData: function($defer, params) {

            deferred.then( function(data) {

              var records = $scope.rankings[$scope.rankingsPeriod];
              var orderedData = orderAndFilterData(records);
              params.total(orderedData.length);  
              $defer.resolve(orderedData.slice((params.page() - 1) * params.count(), params.page() * params.count()));
              $scope.tableInitialized  = true;
            });
        }
      });

      
      
      // Perform a delayed refresh of the table.
      // Delay any filters by 300 millisceonds
      var delayedRefresh = (function () {

        var delayedTimeout = undefined;

        var doIt = function(delay) {

          // If a timeout is already scheduled, don't do anything.
          if(angular.isDefined(delayedTimeout)) {
            return;
          }

          // The callback will undo the timeout.
          var callback = function() {
            // console.log('in callback!');
            if(angular.isDefined($scope.tableParams) &&
               angular.isDefined($scope.tableInitialized)) {
              // console.log('reloading from callback');
              $scope.tableParams.page(1); // Reset the table to page 1.
              $scope.tableParams.reload();
              delayedTimeout = undefined;

            } else {
              // console.log('rescheduling callback');
              delayedTimeout = $timeout(callback, delay);

            }

          };

          delayedTimeout = $timeout(callback, delay);

        };
        return doIt;

      }());


      $scope.$watch("rankingsPeriod", function (newVal, oldVal) {
          if(angular.isDefined(newVal) && newVal !== oldVal) {
            delayedRefresh();
          }

          $scope.$stateParams.timePeriod = newVal;

          $state.go('rankings', $scope.$stateParams, {location: "replace"});
          $location.search($scope.$stateParams); // Update the location
          $location.replace(); // Replace the current location in the browsers history instead of adding a new entry.

      });

      $scope.$watch("unitTypes", function (newVal, oldVal) {

        if(angular.isDefined(newVal) && newVal !== oldVal) {
          delayedRefresh();
        }

        $scope.$stateParams.unitType = newVal;

        $state.go('rankings', $scope.$stateParams, {location: "replace"});
        $location.search($scope.$stateParams);
        $location.replace();

      }, true); // Deep watch

      $scope.$watch("searchString", function (newVal, oldVal) {
        if(angular.isDefined(newVal) && newVal !== oldVal) {
          delayedRefresh(300);
        }

        if (angular.isDefined($scope.searchString)) {
          $scope.$stateParams.searchString = $scope.searchString;

          $state.go('rankings', $scope.$stateParams, {location: "replace"});
          $location.search($scope.$stateParams);
          $location.replace();
        }
      });


  }]);