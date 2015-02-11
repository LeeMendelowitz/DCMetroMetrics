'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.directory
 * @description
 * # Stores and caches the station directory.
 * Service in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')

  .service('directory', ['$http', '$q', 'Unit', 'UnitStatus', 'StationData', function directory($http, $q, Unit, UnitStatus, StationData) {
    
    // AngularJS will instantiate a singleton by calling "new" on this function
    var self = this;

    var directoryUrl = "/json/station_directory.json";
    var recentUpdateUrl = "/json/recent_updates.json";

    var stationDirectory,
        shortNameToData,
        codeToData,
        escalatorOutages,
        elevatorOutages,
        daily_break_count, // Number of new breaks per day. 
        daily_broken_count, // Number of broken units on a day.
        recentUpdates,
        unitIdToUnit,
        escalators,
        elevators;

    var convertStationDirectory = function(data) {
      // Convert station directory from plain objects to
      // StationData objects
      for (var k in data) {
        if (data.hasOwnProperty(k)) {
          data[k] = new StationData(data[k]);
        }
      }
      return data;
    };


    this.get_directory = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();
      var ret;

      if (stationDirectory && shortNameToData && codeToData) {
          ret = { directory: stationDirectory,
                     shortNameToData: shortNameToData,
                     codeToData: codeToData,
                     escalatorOutages: escalatorOutages,
                     elevatorOutages: elevatorOutages,
                     unitIdToUnit: unitIdToUnit } ;
          deferred.resolve(ret);
          return deferred.promise;
      }

      $http.get(directoryUrl, { cache: true })
        .success( function(d) {

          var i, unit;

          stationDirectory = convertStationDirectory(d);

          // Populate shortNameToData;
          shortNameToData = {};
          codeToData = {};
          escalatorOutages = [];
          elevatorOutages = [];

          unitIdToUnit = {};

          for   (var station in stationDirectory) {

            var stationData = stationDirectory[station];
            var shortName = stationData.stations[0].short_name;

            for (i = 0; i < stationData.escalators.length; i++) {
              unit = stationData.escalators[i];
              if (unit.key_statuses.lastStatus.symptom_category !== "ON" ) {
                escalatorOutages.push(unit);
              }
              unitIdToUnit[unit.unit_id] = unit;
            }

            for (i = 0; i < stationData.elevators.length; i++) {
              unit = stationData.elevators[i];
              if (unit.key_statuses.lastStatus.symptom_category !== "ON" ) {
                elevatorOutages.push(unit);
              }
              unitIdToUnit[unit.unit_id] = unit;
            }

            shortNameToData[shortName] = stationData;
            for (i = 0; i < stationData.stations.length; i++) {
              var sdata = stationData.stations[i];
              codeToData[sdata.code] = sdata;
            }

          }

          var ret = {directory: stationDirectory,
                     shortNameToData: shortNameToData,
                     codeToData: codeToData,
                     escalatorOutages: escalatorOutages,
                     elevatorOutages: elevatorOutages,
                     unitIdToUnit: unitIdToUnit };

          deferred.resolve(ret);
          
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };

    this.get_recent_updates = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();
      var ret;

      if (recentUpdates) {
          deferred.resolve(recentUpdates);
          return deferred.promise;
      }

      $http.get(recentUpdateUrl, { cache: true })
        .success( function(d) {
          d = d.map(function(v) { return new UnitStatus(v); });
          recentUpdates = d;
          deferred.resolve(d);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };

    // Get daily break counts.
    this.get_daily_break_count = function() {

      var deferred = $q.defer();

      var ret = { escalators: {},
                  elevators: {}
                };

      if (daily_break_count) {
        deferred.resolve(daily_break_count);
        return deferred.promise;
      }

      self.get_directory().then(

          // on success:
          function(directory) {
            var unit, unit_id, day, day_to_break_count, d;
            var unit_dict = directory.unitIdToUnit;
            for (unit_id in unit_dict) {
              if(unit_dict.hasOwnProperty(unit_id)) {
                unit = new Unit(unit_dict[unit_id]);
                if (unit.isEscalator()) { 
                  d = ret.escalators;
                } else {
                  d = ret.elevators;
                }
                day_to_break_count = unit.performance_summary.all_time.day_to_break_count;
                for(day in day_to_break_count) {
                  if(d.hasOwnProperty(day)) {
                    d[day] += day_to_break_count[day];
                  } else {
                    d[day] = day_to_break_count[day];
                  }
                }
              }
            }

            daily_break_count = ret;
            deferred.resolve(ret);
          },

          // on failure:
          function() {
            deferred.reject("Failed to get directory.");
          }

      );

      return deferred.promise;

    };

    // Get the number of units that had an broken outage by day
    this.get_daily_broken_count = function() {

      var deferred = $q.defer();
      var ret = {escalators: {},
                 elevators: {}
                };

      if (daily_broken_count) {
        deferred.resolve(daily_broken_count);
        return deferred.promise;
      }

      self.get_directory().then(

          // on success:
          function(directory) {
            var unit, unit_id, day, break_days, i, d;
            var unit_dict = directory.unitIdToUnit;
            for (unit_id in unit_dict) {
              if(unit_dict.hasOwnProperty(unit_id)) {
                unit = new Unit(unit_dict[unit_id]);
                if (unit.isEscalator()) { 
                  d = ret.escalators;
                } else {
                  d = ret.elevators;
                }
                break_days = unit.performance_summary.all_time.break_days;
                for(i = 0; i < break_days.length; i++) {
                  day = break_days[i];
                  if(d.hasOwnProperty(day)) {
                    d[day] += 1;
                  } else {
                    d[day] = 1;
                  }
                }
              }
            }

            daily_broken_count = ret;
            deferred.resolve(ret);
          },

          // on failure:
          function() {
            deferred.reject("Failed to get directory.");
          }

      );

      return deferred.promise;

    };

    this.get_unit_dict = function() {

      var deferred = $q.defer();

      if (unitIdToUnit) {
        deferred.resolve(unitIdToUnit);
        return deferred.promise;
      }

      self.get_directory().then( function() {
            deferred.resolve(unitIdToUnit);
          }
      );

      return deferred.promise;

    };


    // Get the station url for a unit.
    this.getStationUrl = function(unit) {

        if(!unit || !codeToData) { return undefined;}
        var sd = codeToData[unit.station_code];
        return "#/stations/" + sd.short_name;

    };

    this.getStationName = function(unit) {
        var sd = unit && codeToData && codeToData[unit.station_code];
        return sd && sd.long_name;
    };

    this.getStationShortName = function(unit) {
        var sd = unit && codeToData && codeToData[unit.station_code];
        return sd && sd.short_name;
    };

    this.codeToShortName = function(station_code) {
        var sd = codeToData && codeToData[station_code];
        return sd && sd.short_name;
    };

    // Get station lines for a unit
    this.getStationLines = function(unit) {

      if (!unit) { return undefined; }

      if (codeToData && unit) {
        var sd = codeToData[unit.station_code];
        return sd && sd.all_lines;
      }

    };

    // Get the unit object for a status
    this.unitFromStatus = function(status) {
      return status && unitIdToUnit &&
       unitIdToUnit[status.unit_id];
    };

    // Get station lines for a status
    this.getStationLinesForStatus = function(status) {
      var unit = status && this.unitFromStatus(status);
      return unit && this.getStationLines(unit);
    };

    this.unitDescription = function(unit){
      var ret = "";
      if (!unit) { return undefined; }
      if (unit.station_desc) {
        ret = unit.station_desc + ", " + unit.esc_desc;
      } else {
        ret = unit.esc_desc;
      }
      return ret;
    };


  }]);
