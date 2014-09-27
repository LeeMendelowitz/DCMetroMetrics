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

    var allReports, allSummaries, dailyCountData;
    var reportsByCar = {};
    var summaryByCar = {};

    var reportsUrl = "/json/hotcar_reports.json";
    var dailyDataUrl = "/json/hotcars_by_day.json";

    // Get hotcar report data
    this.get_data = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();
      var ret;

      if (allReports) {

          ret = { allReports: allReports,
            reportsByCar: reportsByCar,
            summaryByCar: summaryByCar,
            allSummaries: allSummaries } ;
          deferred.resolve(ret);

          return deferred.promise;
      }

      // Compute the one day, three day, seven day
      // 14 day report counts.
      var updateSummary = function(report, now) {

        var summary = summaryByCar[report.car_number];
        var reportTime = new Date(report.time);
        now = now || new Date();
        
        summary.count += 1;

        var oneDay = 24*3600*1000; // oneDay in ms
        if(now - reportTime < oneDay) {summary.d1 += 1;}
        if(now - reportTime < 3*oneDay) {summary.d3 += 1;}
        if(now - reportTime < 7*oneDay) {summary.d7 += 1;}
        if(now - reportTime < 14*oneDay) {summary.d14 += 1;}

      };

      // Get hotcar reports
      $http.get(reportsUrl, { cache: true })
        .success( function(data) {

          allReports = data;
          reportsByCar = {};
          summaryByCar = {};
          allSummaries = [];
          var i, report, reportTime;


          var now = new Date();

          // Loop over all hot car reports and update the various
          // data structures
          for(i = 0; i < allReports.length; i++) {

            report = allReports[i];

            if (reportsByCar.hasOwnProperty(report.car_number)) {

              reportsByCar[report.car_number].push(report);

            } else {

              reportsByCar[report.car_number] = [report];
              summaryByCar[report.car_number] = {  carNumber: report.car_number,
                                                   count: 0,
                                                   d1: 0, // One day count
                                                   d3: 0, // Three day count
                                                   d7: 0, // Seven day count
                                                   d14: 0
                                                };
            }

            updateSummary(report, now);

          }

          // Create a list of all summaries, and sort in descending order of count.
          for( var key in summaryByCar) {
            if (summaryByCar.hasOwnProperty(key)) {
              allSummaries.push(summaryByCar[key]);
            }
          }
          allSummaries.sort(function(s1, s2) { return -(s1.count -  s2.count); });

          var ret = { allReports: allReports,
                      reportsByCar: reportsByCar,
                      summaryByCar: summaryByCar,
                      allSummaries: allSummaries
                    };

          deferred.resolve(ret);
        })
        .error(function() {
          deferred.reject();
        });

      // Return a promise
      return deferred.promise;

    };

    // Get daily data of report counts and temperatures
    this.get_daily_data = function() {
      
      // Return a promise that gives the station directory.
      var deferred = $q.defer();
      var ret;

      if (dailyCountData) {

          ret = dailyCountData ;
          deferred.resolve(ret);

          return deferred.promise;
      }

      // Get hotcar reports
      $http.get(dailyDataUrl, { cache: true })
        .success( function(data) {

          dailyCountData = data;
          var ret = dailyCountData;
          deferred.resolve(ret);

        })
        .error(function() {

          deferred.reject();

        });

      // Return a promise
      return deferred.promise;

    };

  }]);
