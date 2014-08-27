'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.hotCarDirectory
 * @description
 * # hotCarDirectory
 * Service in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .service('hotCarDirectory', ['$http', '$q', function hotCarDirectory($http, $q) {
    // AngularJS will instantiate a singleton by calling "new" on this function

    var allReports;
    var reportsByCar;

    var url = "/json/hotcar_reports.json";

    this.get_data = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();
      var ret;

      if (allReports) {
          ret = { allReports: allReports,
            reportsByCar: reportsByCar } ;
          deferred.resolve(ret);
          return deferred.promise;
      }

      $http.get(url, { cache: true })
        .success( function(data) {

          allReports = data;
          reportsByCar = {};
          var i, report;
          for(i = 0; i < allReports.length; i++) {
            report = allReports[i];
            if (reportsByCar.hasOwnProperty(report.car_number)) {
              reportsByCar[report.car_number].push(report);
            } else {
              reportsByCar[report.car_number] = [report];
            }
          }

          var ret = { allReports: allReports,
                      reportsByCar: reportsByCar };
          deferred.resolve(ret);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };

  }]);
