'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.unitStatus
 * @description
 * # unitStatus
 * Factory in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .factory('UnitStatus', ['$filter', function ($filter) {

    // Service logic
    // ...
    var zone = "America/New_York";

    var UnitStatus = function(data) {

      this.unit_id = data.unit_id;
      this.time = data.time;
      this.is_active = (this.end_time == null);
      this.actual_end_time = data.end_time;
      this.end_time = data.end_time || moment(); // Hack to make end_time now.
      this.metro_open_time = data.metro_open_time;
      this.update_type = data.update_type;
      this.symptom_description = data.symptom_description;
      this.symptom_category = data.symptom_category;

      // Convert times to moments with the East coast time zone
      this.end_time = moment.tz(this.end_time, zone);
      this.actual_end_time = this.actual_end_time && moment.tz(this.actual_end_time, zone);
      this.time = moment.tz(this.time, zone);
      this.start_time = this.time; 
      this.duration = this.end_time - this.start_time;

    };

    UnitStatus.prototype = {

      // Get Days that overlap the status
      getDays : function() {

        var ret = [];
        
        var start_day = this.time.clone().startOf('day');
        var end_day = this.end_time.clone().startOf('day');
        var day = start_day;
        while(day <= end_day) {
          ret.push(day.clone());
          day.add(1, 'd');
        }

        return ret;
        
      },
      isBroken : function() {
        return this.symptom_category === "BROKEN";
      },
      isInspection: function() {
        return this.symptom_category === "INSPECTION";
      },
      isOff: function() {
        return this.symptom_category === "OFF";
      },
      isOperational: function() {
        return this.symptom_category === "ON";
      }


    };

    // Public API here
    return UnitStatus;

  }]);
