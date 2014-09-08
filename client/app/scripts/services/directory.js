'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.directory
 * @description
 * # Stores and caches the station directory.
 * Service in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')

  .service('directory', ['$http', '$q', function directory($http, $q) {
    
    // AngularJS will instantiate a singleton by calling "new" on this function

    var directoryUrl = "/json/station_directory.json";
    var recentUpdateUrl = "/json/recent_updates.json";

    var stationDirectory, shortNameToData, codeToData, escalatorOutages, elevatorOutages;
    var recentUpdates, unitIdToUnit;


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

          stationDirectory = d;

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
              if (unit.key_statuses.lastStatus.symptom_category != "ON" ) {
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
          recentUpdates = d;
          deferred.resolve(d);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
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
