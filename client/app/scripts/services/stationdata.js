'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.stationData
 * @description
 * # StationData
 * Factory in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .factory('StationData', ['Unit', 'UnitStatus', function (Unit, UnitStatus) {
    // Service logic
    // ...

      var StationData = function(data) {

        this.stations = data.stations;
        this.escalators = data.escalators.map(function(d) { return new Unit(d); });
        this.elevators = data.elevators.map(function(d) { return new Unit(d); });
        this.recent_statuses = data.recent_statuses.map(function(d) { return new UnitStatus(d); });

        this.long_name = data.stations[0].long_name;
        this.short_name = data.stations[0].short_name;
        this.all_codes = data.stations[0].all_codes;
        this.all_lines = data.stations[0].all_lines;

      };




      StationData.prototype = {

      };

      // Public API here
      return StationData;

  }]);
