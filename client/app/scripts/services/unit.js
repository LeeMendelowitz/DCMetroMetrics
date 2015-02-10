'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.Unit
 * @description
 * # Unit
 * Factory in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .factory('Unit', ['UnitStatus', function (UnitStatus) {

    // Service logic

    var convertKeyStatuses = function(ks) {
      var k, s;
      for(k in ks) {
        if (ks.hasOwnProperty(k)) {
          s = ks[k];
          if (s) {
            ks[k] = new UnitStatus(s);
          }
        }
      }
      return ks;
    };

    var Unit = function(data) {
      
      this.esc_desc = data.esc_desc;
      this.key_statuses = convertKeyStatuses(data.key_statuses);
      this.performance_summary = data.performance_summary;
      this.station_code = data.station_code;
      this.station_desc = data.station_desc;
      this.station_name = data.station_name;
      this.unit_id = data.unit_id;
      this.unit_type = data.unit_type;

      // Note: The statuses may not be set. Depends on whether the data was requested
      // for a unit's page. The station directory does not include all of the unit statuses.
      this.statuses = data.statuses || [];
      this.statuses = this.statuses.map(function(d) { return new UnitStatus(d); });

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

  }]);
