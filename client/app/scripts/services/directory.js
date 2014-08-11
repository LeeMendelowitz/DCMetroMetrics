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

    var url = "/json/station_directory.json";

    var stationDirectory, shortNameToData, codeToData, escalatorOutages, elevatorOutages;

    this.get_directory = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();
      var ret;

      if (stationDirectory && shortNameToData && codeToData) {
          ret = { directory: stationDirectory,
                     shortNameToData: shortNameToData,
                     codeToData: codeToData,
                     escalatorOutages: escalatorOutages,
                     elevatorOutages: elevatorOutages } ;
          deferred.resolve(ret);
          return deferred.promise;
      }

      $http.get(url, { cache: true })
        .success( function(d) {

          var i, unit;

          stationDirectory = d;

          // Populate shortNameToData;
          shortNameToData = {};
          codeToData = {};
          escalatorOutages = [];
          elevatorOutages = [];
          for   (var station in stationDirectory) {

            var stationData = stationDirectory[station];
            var shortName = stationData.stations[0].short_name;

            for (i = 0; i < stationData.escalators.length; i++) {
              unit = stationData.escalators[i];
              if (unit.key_statuses.lastStatus.symptom_category != "ON" ) {
                escalatorOutages.push(unit);
              }
            }

            for (i = 0; i < stationData.elevators.length; i++) {
              unit = stationData.elevators[i];
              if (unit.key_statuses.lastStatus.symptom_category !== "ON" ) {
                elevatorOutages.push(unit);
              }
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
                     elevatorOutages: elevatorOutages };
          deferred.resolve(ret);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };

  }]);
