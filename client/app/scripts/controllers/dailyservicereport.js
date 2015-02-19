'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:DailyservicereportCtrl
 * @description
 * # DailyservicereportCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('DailyServiceReportCtrl', ['$scope', 'Page', '$state', '$stateParams', '$timeout', 'directory', 'statusTableUtils',
    function ($scope, Page, $state, $stateParams, $timeout, directory, statusTableUtils) {
      
      Page.title("DC Metro Metrics: Daily Service Report");
      Page.description("Daily service report for escalators and elevators in the WMATA Metrorail system in Washington DC.");

      $scope.$stateParams = $stateParams;
      $scope.$state = $state;
      $scope.day_string = $stateParams.day;
      $scope.day = moment($scope.day_string, "YYYY_MM_DD");
      $scope.directory = directory;
      $scope.statusTableUtils = statusTableUtils;
      $scope.dt = $scope.day.toDate();
      $scope.moment = moment;

      function unique(vals) {

        var s = {};
        var ks = [];
        for(var i =0; i < vals.length; i++) {

          if (s.hasOwnProperty(vals[i])) {
            continue;
          }
          s[vals[i]] = true;
          ks.push(vals[i]);
        }
        return ks;

      }

      function split_statuses(statuses) {
        var broken = [];
        var inspections = [];
        var off = [];
        var i, s;
        
        for (i = 0; i < statuses.length; i++) {

          s = statuses[i];

          if (s.isBroken()) {
            broken.push(s);
          } else if ( s.isOff() ) {
            off.push(s);
          } else if (s.isInspection() ) {
            inspections.push(s);
          }

        }

        var broken_unit_ids = broken.map(function(s) { return s.unit_id; });
        var inspected_unit_ids = inspections.map(function(s) { return s.unit_id; });


        return {broken : broken,
                inspections: inspections,
                off: off,
                num_units_broken: unique(broken_unit_ids).length,
                num_units_inspected: unique(inspected_unit_ids).length
               };

      }

      directory.get_daily_service_report($scope.day_string).then(function(data) {

        $scope.report = data;

        // Categorize the statuses
        $scope.escalators = split_statuses(data.escalators.statuses);
        $scope.elevators = split_statuses(data.elevators.statuses);

        $scope.no_escalator_broken = $scope.escalators.broken.length == 0;
        $scope.no_escalator_inspection = $scope.escalators.inspections.length == 0;
        $scope.no_escalator_off = $scope.escalators.off.length == 0;

        $scope.no_elevator_broken = $scope.elevators.broken.length == 0;
        $scope.no_elevator_inspection = $scope.elevators.inspections.length == 0;
        $scope.no_elevator_off = $scope.elevators.off.length == 0;

      },

      function() {

        console.log("Error getting daily service report!");
        $scope.loadingError = true;

      });



      $scope.forceDate = function() {

        $scope.dt = new Date(2014, 1, 1);

      }

      // Date picker stuff
      $scope.today = function() {
        $scope.dt = new Date();
      };


      $scope.clear = function () {
        $scope.dt = null;
      };

      $scope.minDate = new Date(2013, 6 - 1, 1); // June 1
      $scope.maxDate = moment().startOf('day').subtract(1, "days").toDate();
      $scope.opened = false;

      $scope.open = function($event) {
        $event.preventDefault();
        $event.stopPropagation();
        $scope.opened = true;
      };

      $scope.dateOptions = {
        formatYear: 'yy',
        startingDay: 1
      };

      $scope.format = 'shortDate';

      var defaultHelp = "Bad date provided.";
      var outOfRangeHelp = "Date must be between 6/1/13 and " + moment($scope.maxDate).format("M/D/YY");
      $scope.helpMsg = "";

      $scope.dateIsValid = function(){

        // return true if the date is valid
        if (!$scope.dt) { 
          $scope.helpMsg = defaultHelp;
          return false;
        }

        var m = moment($scope.dt)

        if (!m.isValid()) {
          $scope.helpMsg = defaultHelp;
          return false;
        }

        if (m < $scope.minDate || m > $scope.maxDate) {
          $scope.helpMsg = outOfRangeHelp;
          $scope.dateOutOfRange = true;
          return false;
        }

        $scope.helpMsg = "";
        return true;
      }


      $scope.dateIsInvalid = function() {
        return !$scope.dateIsValid();
      }

      $scope.submitDate = function() {

        $scope.badDate = $scope.dateIsInvalid();
        if (!$scope.badDate) {
          // Check that the date is valid.
          $timeout.cancel(submitTimer);
          $timeout.cancel(formStyleTimer);
          $state.go('dailyservicereport', {day : moment($scope.dt).format("YYYY_MM_DD")});
        }

      };

      $scope.badDate = $scope.dateIsInvalid(); // Is the date valid?

      var submitTimer = undefined;
      var formStyleTimer = undefined;

      // Look for changes to dt. Update form styles
      // and submit the form via timers.
      $scope.$watch("dt", function(newVal) {
        
        submitTimer = submitTimer || $timeout(function() {
          $scope.badDate = $scope.dateIsInvalid();
          $scope.submitDate();
          submitTimer = undefined;
        }, 500);


      });





  }]);
