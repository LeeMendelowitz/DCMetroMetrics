'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.Unit
 * @description
 * # Unit
 * Factory in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .factory('Unit', function () {

    // Service logic


    var Unit = function(data) {
      
      this.esc_desc = data.esc_desc;
      this.key_statuses = data.key_statuses;
      this.performance_summary = data.performance_summary;
      this.station_code = data.station_code;
      this.station_desc = data.station_desc;
      this.station_name = data.station_name;
      this.unit_id = data.unit_id;
      this.unit_type = data.unit_type;

    };


    Unit.prototype = {
      isEscalator: function() {
        return this.unit_type === "ESCALATOR";
      },
      isElevator: function() {
        return this.unit_type === "ELEVATOR";
      }
    };

    // Public API here
    return Unit;

  });
