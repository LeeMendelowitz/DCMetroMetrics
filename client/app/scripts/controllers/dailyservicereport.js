'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:DailyservicereportCtrl
 * @description
 * # DailyservicereportCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('DailyServiceReportCtrl', ['$scope', '$rootScope', 'Page', '$state', '$stateParams', '$timeout',
    'directory', 'statusTableUtils', 'usSpinnerService', '$scrollspy',
    function ($scope, $rootScope,  Page, $state, $stateParams, $timeout, directory, statusTableUtils, usSpinnerService, $scrollspy) {
      
      Page.title("DC Metro Metrics: Daily Service Report");
      Page.description("Daily service report for escalators and elevators in the WMATA Metrorail system in Washington DC.");

      var zone = "America/New_York";

      $scope.$stateParams = $stateParams;
      $scope.$state = $state;
      $scope.directory = directory;
      $scope.statusTableUtils = statusTableUtils;
      $scope.haveData = false;

      var computeMaxDate = function() {

        // I think we need to strip timezone to get this to work.
        var now = moment().tz(zone);
        var day_start = moment().tz(zone).hour(7).minute(0).second(0);
        if(now > day_start) {
          // Can use today
          return day_start.startOf('day').toDate();
        }

        return day_start.subtract(1, "day").startOf('day').toDate();

      };

      $scope.minDate = moment().tz(zone).month(5).day(1).year(2013).startOf('day').toDate(); // June 1. Months are zero indexed!
      $scope.maxDate = computeMaxDate(); // Last day we should have data for.


      // We have three models the date - they are coupled through watches.
      $scope.dt_picker = undefined; // The picker's model for date
      $scope.dt_input = undefined; // The input's model for the date. As user types, this will temporarily have bad dates
      $scope.dt = undefined; // The "true" date of the page (i.e. what data we are showing.) This changes via the datepicker and input.

      // Initialize from the url.
      $scope.day_string = $stateParams.day;
      $scope.day = moment($scope.day_string, "YYYY_MM_DD").tz(zone);
      $scope.dt = ($scope.day.isValid() && $scope.day.toDate()) || undefined;
      $scope.dt_picker = $scope.dt;
      $scope.dt_input = $scope.dt && moment($scope.dt).format("M/D/YY");

      // If the date hasn't been provided, use maxDate (the most recent day we should have data for).
      if(!$scope.dt) {
        $scope.dt = $scope.maxDate;
        $scope.dt_input = moment($scope.dt).format("M/D/YY");
        $scope.dt_picker = $scope.dt;
        $scope.day_string = moment($scope.maxDate).tz(zone).format("YYYY_MM_DD");

        $state.go('dailyservicereport', {day : moment($scope.maxDate).tz(zone).format("YYYY_MM_DD")});
      }


      // Functions to help keep things in sync
      var updateFromPicker = function() {
        if($scope.dt_picker && $scope.dt_picker !== $scope.dt && dateIsValid($scope.dt_picker)) {
          $scope.dt = $scope.dt_picker;
          $scope.dt_input = moment($scope.dt).format("M/D/YY");
          $scope.submitDate();
        }
      };

      var inputTimer;
      $scope.$watch('dt_picker', function(newVal) {

        // Time this out as a user types
        $timeout.cancel(inputTimer);
        inputTimer = $timeout(function() {
            updateFromPicker();
            inputTimer = undefined;
          }, 100);
        
      });


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
        var symptom_to_count = {};
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

          if (symptom_to_count.hasOwnProperty(s.symptom_description)) {
            symptom_to_count[s.symptom_description] += 1;
          } else {
            symptom_to_count[s.symptom_description] = 1;
          }

        }

        var broken_unit_ids = broken.map(function(s) { return s.unit_id; });
        var inspected_unit_ids = inspections.map(function(s) { return s.unit_id; });


        return {broken : broken,
                inspections: inspections,
                off: off,
                num_units_broken: unique(broken_unit_ids).length,
                num_units_inspected: unique(inspected_unit_ids).length,
                symptom_to_count: symptom_to_count,
                num_statuses : statuses.length
               };

      }

      if($scope.day_string) {

        usSpinnerService.spin('daily-service-report');

        directory.get_daily_service_report($scope.day_string).then(function(data) {

          $scope.report = data;

          // Categorize the statuses
          $scope.escalators = split_statuses(data.escalators.statuses);
          $scope.elevators = split_statuses(data.elevators.statuses);

          $scope.no_escalator_broken = $scope.escalators.broken.length === 0;
          $scope.no_escalator_inspection = $scope.escalators.inspections.length === 0;
          $scope.no_escalator_off = $scope.escalators.off.length === 0;

          $scope.no_elevator_broken = $scope.elevators.broken.length === 0;
          $scope.no_elevator_inspection = $scope.elevators.inspections.length === 0;
          $scope.no_elevator_off = $scope.elevators.off.length === 0;

          $scope.haveData = true;

          // Get a list of unique symptom descriptions for the day.
          var symptom_count_dict = {};

          angular.forEach($scope.escalators.symptom_to_count, function(val, key) {
            if(symptom_count_dict.hasOwnProperty(key)) {
                symptom_count_dict[key].escalators = val;
            } else {
                symptom_count_dict[key] = {symptom: key, escalators: val};
            }
          });

          angular.forEach($scope.elevators.symptom_to_count, function(val, key) {
            if(symptom_count_dict.hasOwnProperty(key)) {
                symptom_count_dict[key].elevators = val;
            } else {
                symptom_count_dict[key] = {symptom: key, elevators: val};
            }
          });

          $scope.symptom_description_counts = [];
          angular.forEach(symptom_count_dict, function(val, key){ $scope.symptom_description_counts.push(val); });



          usSpinnerService.stop('daily-service-report');
        

          //////////////////////////////////////////////////////////////////////////////////////
          // Broadcast that we have received data
          //
          // This is a total hack in a way - when this function executes, we are populating values in the $scope,
          // which will update the DOM in the view. We need to let scrollspy about this so it can recompute
          // positions. 
          //
          // On option is to emit a '$viewContentLoaded' event, because scrollSpy listens for that.
          // Another option is to deal with scrollspy itself. 
          // Let's emit the event after the this digest, which *should* work.
          //
          // It's a hack, because we could be better organized by using $state and having a haveData state or something similar.
          $timeout(function() {
            $rootScope.$broadcast('dcmm-data-load', 'data-here?');
            $rootScope.$broadcast('$viewContentLoaded');
          }, false); // false because we don't need to redo dirty checking.

        },

        function() {

          console.log("Error getting daily service report!");
          usSpinnerService.stop('daily-service-report');
          $scope.loadError = true;

        });


      }



      $scope.forceDate = function() {

        $scope.dt_picker = new Date(2014, 1, 1);

      };

      // Date picker stuff
      $scope.today = function() {
        $scope.dt_picker = new Date();
      };


      $scope.clear = function () {
        $scope.dt_picker = null;
      };



      $scope.opened = false;

      $scope.open = function($event) {
        $event.preventDefault();
        $event.stopPropagation();
        $scope.opened = true;
      };

      $scope.toggle = function($event) {
        $event.preventDefault();
        $event.stopPropagation();
        $scope.opened = !$scope.opened;
      };

      $scope.dateOptions = {
        formatYear: 'yy',
        startingDay: 1,
        'currentText': 'Most Recent'
      };

      $scope.format = 'shortDate';

      var defaultHelp = "Bad date provided.";
      var outOfRangeHelp = "Date must be between 6/1/13 and " + moment($scope.maxDate).tz(zone).format("M/D/YY");
      $scope.helpMsg = "";

      var dateIsValid = function(date_val){

        // return true if the date is valid
        if (!date_val) { 
          $scope.helpMsg = defaultHelp;
          return false;
        }

        var m = moment(date_val).tz(zone);

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
      };


      var dateIsInvalid = function(date_val) {
        return !dateIsValid(date_val);
      };

      $scope.submitDate = function() {

        $scope.badDate = dateIsInvalid($scope.dt);
        if (!$scope.badDate) {
          $state.go('dailyservicereport', {day : moment($scope.dt_picker).tz(zone).format("YYYY_MM_DD")});
        }

      };

      $scope.badDate = dateIsInvalid($scope.dt); // Is the date valid?




  }]);
