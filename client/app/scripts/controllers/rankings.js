'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:RankingsCtrl
 * @description
 * # RankingsCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('RankingsCtrl', ['$scope', '$state', 'directory', 'queryParser', 'ngTableParams', '$filter',
    '$timeout', '$stateParams', '$location',

     function ($scope, $state, directory, queryParser, ngTableParams, $filter, $timeout, $stateParams, $location) {

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

      var parseSortingFromString = function(sortString) {

        if(!angular.isDefined(sortString) || sortString === "" || sortString === null) {
          return;
        }
        var sortChar = sortString.substring(0, 1);
        var sortCol = sortString.substring(1);
        var sort = { };
        sort[sortCol] = sortChar === "+" ? "asc" : "desc";
        return sort;
      };

      $scope.sort = parseSortingFromString($scope.$stateParams.orderBy) || 
        {broken_time_percentage: 'desc'};


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



      var unitsFilter = function(data, index) {
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

        // Apply unit filter
        var filtered_records = $filter('filter')(orderedData, unitsFilter);

        // Apply the search pattern
        try {

          if ($scope.searchString !== "") {

            var matchHandler = searchStringParser.parse($scope.searchString);

            filtered_records = $filter('filter')( filtered_records, function(rec) {
              return matchHandler(queryParser.matcherFunction, rec)
            });

          }

        } catch (e) {

          if (e instanceof searchStringParser.SyntaxError) {
            console.log("Caught somethign!", e);
            filtered_records =  [];
          } else {
            throw e;
          }

        }


        // filtered_records = $filter('filter')( filtered_records, {$: $scope.searchString} );
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

        // Get rankings for the specified time period. Return an array
        // of records.
        var getRankings = function(rankings_key) {
          
          var unit_data, station_data, unit, record;
          var records = [];

          for(var unitId in data.unitIdToUnit) {

            if(!data.unitIdToUnit.hasOwnProperty(unitId)) {
              continue;
            }

            unit_data = data.unitIdToUnit[unitId];
            station_data = data.codeToData[unit_data.station_code];

            record = {unit: unit_data,
                      unit_id: unit_data.unit_id,
                      unit_type: unit_data.unit_type,
                      station: station_data.long_name,
                      station_code: unit_data.station_code,
                      station_lines: station_data.all_lines,
                      station_desc: unit_data.station_desc,
                      esc_desc: unit_data.esc_desc };
            
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
          sorting: $scope.sort
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

      

      // Perform a delayed call. If interrupted,
      // by an additional call, reschedule the timeout.
      // If the callback returns true, reschedule the callback.
      var makeDelay = function () {

        var delayedTimeout = undefined;

        var doIt = function(callback, delay) {

          // If a timeout is already scheduled, cancel it.
          if(angular.isDefined(delayedTimeout)) {
            // console.log("cancelling timeout!")
            $timeout.cancel(delayedTimeout);
          }

          var wrappedCall = function() {
            // console.log("in wrapped call");

            var ret = callback();
            if (ret === true) {
              // console.log("rescheduling timeout");
              $timeout.cancel(delayedTimeout);
              delayedTimeout = $timeout(wrappedCall, delay);
            } else {
              // console.log("done with wrapped called.")
              $timeout.cancel(delayedTimeout);
              delayedTimeout = undefined;
            }

          };

          delayedTimeout = $timeout(wrappedCall, delay);

        };

        return doIt;

      };

      // Define the callback for performing a table refresh
      var delayedTableRefreshCallback = function() {

            if(angular.isDefined($scope.tableParams) &&
               angular.isDefined($scope.tableInitialized)) {
              
              $scope.tableParams.page(1); // Reset the table to page 1.
              $scope.tableParams.reload();
              return false;

            } else {
              // console.log('rescheduling callback');
              return true; // reschedule the timeout
            }

      };

      var tableRefreshDelay = makeDelay();
      var searchStringDelay = makeDelay();

      // Schedule a delayed table refresh
      var delayedTableRefresh = function(delay) {
        tableRefreshDelay(delayedTableRefreshCallback, delay);
      };

      $scope.$watch("rankingsPeriod", function (newVal, oldVal) {

          if(angular.isDefined(newVal) && newVal !== oldVal) {
            delayedTableRefresh();
          }

          $scope.$stateParams.timePeriod = newVal;

          $state.go('rankings', $scope.$stateParams, {location: "replace"});
          $location.search($scope.$stateParams); // Update the location
          $location.replace(); // Replace the current location in the browsers history instead of adding a new entry.

      });

      $scope.$watch("unitTypes", function (newVal, oldVal) {

        if(angular.isDefined(newVal) && newVal !== oldVal) {
          delayedTableRefresh();
        }

        $scope.$stateParams.unitType = newVal;

        $state.go('rankings', $scope.$stateParams, {location: "replace"});
        $location.search($scope.$stateParams);
        $location.replace();

      }, true); // Deep watch

      $scope.$watch("searchString", function (newVal, oldVal) {

        if(angular.isDefined(newVal) && newVal !== oldVal) {

          delayedTableRefresh(300);

          searchStringDelay(function() {
            
            if (angular.isDefined($scope.searchString)) {
              $scope.$stateParams.searchString = $scope.searchString;

              $state.go('rankings', $scope.$stateParams, {location: "replace"});
              $location.search($scope.$stateParams);
              $location.replace();
            }
          }, 300);

        };
        
      });

      // Update state params when the table sort changes
      $scope.$watch("tableParams.sorting()", function (newVal, oldVal) {
        $scope.$stateParams.orderBy = $scope.tableParams.orderBy();
        $state.go('rankings', $scope.$stateParams, {location: "replace"});
        $location.search($scope.$stateParams);
        $location.replace();
      });



  }]);