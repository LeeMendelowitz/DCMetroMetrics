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
          OFF : 'warning',
          ON : 'success',
          REHAB : 'info'
    };

    
    this.getRowClass = function(status) {
        var category = status.symptom_category;
        return catToClass[category];
    };

    this.getDuration = function(status) {
      var end_time = status.end_time ? new Date(status.end_time) : new Date();
      var start_time = new Date(status.time);
      var duration = end_time - start_time;
      return duration;
    };

    this.getTimeSince = function(status) {
      var start_time = new Date(status.time);
      var timeSince = (new Date()) - start_time;
      return timeSince;
    };



  });
