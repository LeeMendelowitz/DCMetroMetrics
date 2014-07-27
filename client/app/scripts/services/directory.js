'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.directory
 * @description
 * # directory
 * Service in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')

  .service('directory', ['$http', '$q', function directory($http, $q) {
    
    // AngularJS will instantiate a singleton by calling "new" on this function

    var url = "/json/station_directory.json";

    var stationDirectory, shortNameToData;

    this.get_directory = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();

      $http.get(url, { cache: true })
        .success( function(d) {

          stationDirectory = d;

          // Populate shortNameToData;
          shortNameToData = {};
          for   (var station in stationDirectory) {
            var stationData = stationDirectory[station];
            var shortName = stationData.stations[0].short_name;
            shortNameToData[shortName] = stationData;
          }

          var ret = {directory: stationDirectory,
                     shortNameToData: shortNameToData };
          deferred.resolve(ret);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };

  }]);
