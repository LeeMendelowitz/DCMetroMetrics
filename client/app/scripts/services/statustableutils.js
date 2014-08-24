'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.statusTableUtils
 * @description
 * # statusTableUtils
 * Service in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .service('statusTableUtils', function statusTableUtils() {
    // AngularJS will instantiate a singleton by calling "new" on this function
    
    // Status category to table class
    var catToClass = {
          BROKEN : 'danger',
          INSPECTION : 'warning',
          OFF : 'danger',
          ON : 'success',
          REHAB : 'info'
    };

    var now = new Date();

    var getNow = function() {
      var newNow = new Date();
      var isStale = (newNow - now) < 60*1000;
      if (isStale) {
        now = newNow;
      }
      return now;
    };

    
    this.getRowClass = function(status) {
        var category = status.symptom_category;
        return catToClass[category];
    };

    this.getDuration = function(status) {
      var end_time = status.end_time ? new Date(status.end_time) : getNow();
      var start_time = new Date(status.time);
      var duration = end_time - start_time;
      return duration;
    };


  });
