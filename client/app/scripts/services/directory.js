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

    var stationDirectory, shortNameToData, codeToData;

    this.get_directory = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();
      var ret;

      if (stationDirectory && shortNameToData && codeToData) {
          ret = { directory: stationDirectory,
                     shortNameToData: shortNameToData,
                     codeToData: codeToData } ;
          deferred.resolve(ret);
          return deferred.promise;
      }

      $http.get(url, { cache: true })
        .success( function(d) {

          stationDirectory = d;

          // Populate shortNameToData;
          shortNameToData = {};
          codeToData = {};
          for   (var station in stationDirectory) {
            var stationData = stationDirectory[station];
            var shortName = stationData.stations[0].short_name;
            shortNameToData[shortName] = stationData;
            for (var i = 0; i < stationData.stations.length; i++) {
              var sdata = stationData.stations[i];
              codeToData[sdata.code] = sdata;
            }
          }

          var ret = {directory: stationDirectory,
                     shortNameToData: shortNameToData,
                     codeToData: codeToData };
          deferred.resolve(ret);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };

  }]);
