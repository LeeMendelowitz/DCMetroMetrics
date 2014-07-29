'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.unitService
 * @description
 * # unitService
 * Service in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .service('unitService', ['$http', '$q', function unitService($http, $q) {
    // AngularJS will instantiate a singleton by calling "new" on this function


    var unitToData = {};

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
