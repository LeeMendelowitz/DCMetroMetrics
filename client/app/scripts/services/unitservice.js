'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.unitService
 * @description
 * # unitService
 * Service in the dcmetrometricsApp for handling data for a unit.
 */
angular.module('dcmetrometricsApp')
  .service('unitService', ['$http', '$q', 'UnitStatus', function unitService($http, $q, UnitStatus) {
    // AngularJS will instantiate a singleton by calling "new" on this function


    var unitToData = {};


    // Convert break counts to a format that
    // is friendly for Cal-heatmap: http://kamisama.github.io/cal-heatmap/
    // This requires dates to be given as seconds since Jan 1 1970
    var fixDateToBreakCount = function(data) {
      var ps = data.performance_summary.all_time;
      var d2bk = ps.day_to_break_count;
      ps.day_seconds_to_break_count = {};
      for(var key in d2bk) {
        if(d2bk[key]) {
          var d = moment(key);
          ps.day_seconds_to_break_count[d.unix()] = d2bk[key];
        }
      }

      data.day_to_break_count = ps.day_seconds_to_break_count;

    };

    // Compute days where an outage overlapped.
    var computeOutageDays = function(data) {

      var ss = data.statuses_objs;
      var d = {};
      var i, j, s, days;

      for(i = 0; i < ss.length; i++) {
        
        s = ss[i];

        if(s.symptom_category === "OFF" ||
           s.symptom_category === "BROKEN") {

          days = s.getDays();
          for(j = 0; j < days.length; j++) {
            // Get the seconds of the day start
            d[days[j].unix()] = 1;
          }

        }

      }

      data.day_has_outage = d;

    };

    // Compute days where an outage overlapped.
    var computeRehabDays = function(data) {

      var ss = data.statuses_objs;
      var d = {};
      var i, j, s, days;

      for(i = 0; i < ss.length; i++) {
        
        s = ss[i];

        if(s.symptom_category === "REHAB") {

          days = s.getDays();
          for(j = 0; j < days.length; j++) {
            // Get the seconds of the day start
            d[days[j].unix()] = 1;
          }

        }

      }

      data.day_has_rehab = d;

    };

    // Compute days where an outage overlapped.
    var computeInspectionDays = function(data) {

      var ss = data.statuses_objs;
      var d = {};
      var i, j, s, days;

      for(i = 0; i < ss.length; i++) {
        
        s = ss[i];

        if(s.symptom_category === "INSPECTION") {

          days = s.getDays();
          for(j = 0; j < days.length; j++) {
            // Get the seconds of the day start
            d[days[j].unix()] = 1;
          }

        }

      }

      data.day_has_inspection = d;

    };



    this.getUnitData = function(unitId) {

      
      // Return a promise that gives the unit data
      var deferred = $q.defer();

      // See if we have cached the data already
      if (unitToData[unitId]) {
        deferred.resolve(unitToData[unitId]);
        return deferred.promise;
      }

      var url = "/json/units/" + unitId + ".json";
      $http.get(url, { cache: true })
        .success( function(data) {

          data.statuses_objs = data.statuses.map(function(d) { return new UnitStatus(d); });
          fixDateToBreakCount(data);
          computeOutageDays(data);
          computeInspectionDays(data);
          computeRehabDays(data);

          unitToData[unitId] = data;
          deferred.resolve(data);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };


    
  }]);
